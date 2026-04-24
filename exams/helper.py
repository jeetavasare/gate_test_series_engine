import re
from django.conf import settings
from collections import defaultdict
from .config import *

def safe_div(num, den):
    return (num / den) if den else 0

def time_mins_to_hour_mins(time_mins):
    hours, mins = divmod(time_mins or 0, 60)
    if hours > 0:
        return f"{hours}hr{'s' if hours > 1 else ''} {f'{mins}min' if mins > 0 else ''}".strip()
    else:
        return f"{mins}min"
    
def time_seconds_to_mins_seconds(time_seconds):
    mins, seconds = divmod(time_seconds or 0, 60)
    if mins > 0:
        return f"{mins}min{'s' if mins > 1 else ''} {f'{seconds}sec' if seconds > 0 else ''}".strip()
    else:
        return f"{seconds}sec"
    

def replace_question_image_link(question_html):
    static_prefix = settings.STATIC_URL

    if 'gateoverflow_exam_images' in question_html:
            question_html = re.sub(
                r'src=["\'](gateoverflow_exam_images/[^"\']+)["\']', 
                rf'src="{static_prefix}\1"', 
                question_html
            )
    return question_html

def calculate_attempt_performance(exam, attempt, exam_questions, user_responses):
    sections = {
        'General Aptitude': {'questions': [], 'marks': 0, 'marks_obtained': 0, 'time_spent_secs': 0}, 
        'Technical': {'questions': [], 'marks': 0, 'marks_obtained': 0, 'time_spent_secs': 0}
    }
    total_marks_obtained = 0.0

    perf = {
        '1m_attempts': 0, '2m_attempts': 0, 'total_attempts': 0,
        '1m_correct': 0, '2m_correct': 0, '1m_incorrect': 0, '2m_incorrect': 0,
        '1m_skipped': 0, '2m_skipped': 0, '1m_total_q': 0, '2m_total_q': 0, '1m_total_m':0, '2m_total_m': 0,
        '1m_attempted_m': 0, '2m_attempted_m': 0,
        '1m_correct_m': 0, '2m_correct_m': 0,
        '1m_penalty_m': 0.0, '2m_penalty_m': 0.0,
        'highest_time_sec': 0
    }

    subject_wise_break_down = defaultdict(lambda: {
            "count": 0,
            # "1m_count": 0,
            # "2m_count": 0,
            "total_marks": 0,
            "total_attempts": 0,
            # "1m_marks":0,
            # "2m_marks": 0,
            # "1m_correct": 0,
            # "2m_correct": 0,
            # "1m_correct_m": 0,
            # "2m_correct_m": 0,
            "total_correct": 0,
            # "1m_incorect": 0,
            # "2m_incorrect": 0,
            # "total_incorrect": 0,
            # "1m_skipped": 0,
            # "2m_skipped": 0,
            # "total_skipped": 0,
            "marks_scored": 0,
            "overall_accuracy": 0
        })
    # Cols: total questions(), scored()/total marks(), total corrcet(), total_incorrect(), total_skipped(), 

    for eq in exam_questions:
        q_id = eq.question.q_id
        resp = user_responses.get(q_id, {})

        eq.user_ans = resp.get('ans')
        eq.time_taken_sec = resp.get('time_sec', 0)
        eq.color_class = ''

        
        eq.time_taken_class = ''
        if eq.time_taken_sec >= 180:
            eq.time_taken_class = 'text-warning'
        # Assign order for Python sorting (Future shuffle proof)
        eq.display_order = resp.get('presented_order', eq.original_order or q_id)
        eq.q_status = resp.get('q_status')
        
        try:
            eq.formatted_time_taken = time_seconds_to_mins_seconds(eq.time_taken_sec)
        except NameError:
            eq.formatted_time_taken = f"{eq.time_taken_sec}s"

        perf['highest_time_sec'] = max(perf['highest_time_sec'], eq.time_taken_sec)

        marks_award = eq.question.marks_award
        marks_penalty = eq.question.marks_penalty 
        question_category = eq.question.category
        correct_answer = eq.question.correct_answer
        is_correct = False
        m_key = f"{int(marks_award)}m"
        perf[f'{m_key}_total_q'] += 1
        perf[f'{m_key}_total_m'] += marks_award

        if eq.question.correct_answer == 'X':
            total_marks_obtained += marks_award
            eq.ans_status = 'Marks To All'
            eq.color_class = 'bg-info'
            perf['total_attempts'] += 1
            perf[f'{m_key}_attempts'] += 1
            perf[f'{m_key}_attempted_m'] += marks_award
            perf[f'{m_key}_correct'] += 1
            perf[f'{m_key}_correct_m'] += marks_award
            
        elif eq.user_ans:
            perf['total_attempts'] += 1
            perf[f'{m_key}_attempts'] += 1
            perf[f'{m_key}_attempted_m'] += marks_award

            subject_wise_break_down[question_category]['total_attempts'] += 1
            
            if ":" in correct_answer:
                try:
                    min_val, max_val = map(float, correct_answer.split(':'))
                    if min_val <= float(eq.user_ans) <= max_val:
                        is_correct = True
                except:
                    pass
            else:
                if correct_answer == eq.user_ans:
                    is_correct = True

            if is_correct:
                subject_wise_break_down[question_category]['total_correct'] += 1
                subject_wise_break_down[question_category]['marks_scored'] += marks_award
                total_marks_obtained += marks_award
                perf[f'{m_key}_correct'] += 1
                perf[f'{m_key}_correct_m'] += marks_award
                eq.ans_status = 'Correct'
                eq.color_class = 'bg-success'
            else:
                subject_wise_break_down[question_category]['marks_scored'] -= marks_penalty
                total_marks_obtained -= marks_penalty
                perf[f'{m_key}_incorrect'] += 1
                perf[f'{m_key}_penalty_m'] += marks_penalty
                eq.ans_status = 'Incorrect'
                eq.color_class = 'bg-warning text-dark' if marks_penalty == 0 else 'bg-danger'
        else:
            perf[f'{m_key}_skipped'] += 1
            eq.ans_status = 'Skipped'

        if 'aptitude' in eq.question.category.lower():
            # HERE WE DO NOT ACCOUNT FOR MARKS FOR ALL QUESTION
            if is_correct:
                sections['General Aptitude']['marks_obtained'] += marks_award
            else:
                sections['General Aptitude']['marks_obtained'] -= marks_penalty

            sections['General Aptitude']['questions'].append(eq)
            sections['General Aptitude']['marks'] += eq.question.marks_award
            
            sections['General Aptitude']['time_spent_secs'] += eq.time_taken_sec
        else:
            # HERE WE DO NOT ACCOUNT FOR MARKS FOR ALL QUESTION
            if is_correct:
                sections['Technical']['marks_obtained'] += marks_award
            else:
                sections['Technical']['marks_obtained'] += marks_penalty
            sections['Technical']['questions'].append(eq)
            sections['Technical']['marks'] += eq.question.marks_award

            sections['Technical']['time_spent_secs'] += eq.time_taken_sec

        subject_wise_break_down[question_category]['count'] += 1
        subject_wise_break_down[question_category]['total_marks'] += marks_award

    sections['General Aptitude']['time_spent_secs'] = time_seconds_to_mins_seconds(sections['General Aptitude']['time_spent_secs'])
    sections['Technical']['time_spent_secs'] = time_seconds_to_mins_seconds(sections['Technical']['time_spent_secs'])
    
    # Create a reverse mapping for O(1) pool lookup, {Subject: Poolname}
    subject_to_pool = {sub: pool for pool, subs in pool_mapping.items() for sub in subs}

    pooled_data = {}

    for category in subject_wise_break_down:
        # --- Your original explicit logic ---
        subject_wise_break_down[category]['overall_accuracy'] = safe_div(subject_wise_break_down[category]['total_correct'] , subject_wise_break_down[category]['total_attempts'])*100
        subject_wise_break_down[category]['score'] = safe_div(subject_wise_break_down[category]['marks_scored'] , subject_wise_break_down[category]['total_marks'])*100
        
        accuracy_class = ""
        if subject_wise_break_down[category]['overall_accuracy'] >= 70:
            accuracy_class = 'text-success'
        elif 40 < subject_wise_break_down[category]['overall_accuracy'] < 70 :
            accuracy_class = 'text-warning-emphasis'
        else:
            accuracy_class = 'text-danger'

        score_class = ""
        if subject_wise_break_down[category]['score'] >= 70:
            score_class = 'text-success'
        elif 40 < subject_wise_break_down[category]['score'] < 70 :
            score_class = 'text-warning-emphasis'
        else:
            score_class = 'text-danger'

        subject_wise_break_down[category]['accuracy_class'] = accuracy_class
        subject_wise_break_down[category]['score_class'] = score_class

        # --- Flat Pool Aggregation ---
        pool_name = subject_to_pool.get(category)
        
        if pool_name:
            if pool_name not in pooled_data:
                pooled_data[pool_name] = {
                    'subjects_list': [], 
                    'count': 0, 
                    'total_attempts': 0, 
                    'total_correct': 0, 
                    'total_marks': 0.0, 
                    'marks_scored': 0.0
                }
            
            pooled_data[pool_name]['subjects_list'].append(category)
            pooled_data[pool_name]['count'] += subject_wise_break_down[category].get('count', 0)
            pooled_data[pool_name]['total_attempts'] += subject_wise_break_down[category].get('total_attempts', 0)
            pooled_data[pool_name]['total_correct'] += subject_wise_break_down[category].get('total_correct', 0)
            pooled_data[pool_name]['total_marks'] += subject_wise_break_down[category].get('total_marks', 0.0)
            pooled_data[pool_name]['marks_scored'] += subject_wise_break_down[category].get('marks_scored', 0.0)

    # --- Post-process pools to create comma string and apply your class logic ---
    for pool_name, p_data in pooled_data.items():
        p_data['subjects'] = ", ".join(p_data.pop('subjects_list'))
        
        p_data['overall_accuracy'] = safe_div(p_data['total_correct'], p_data['total_attempts']) * 100
        p_data['score'] = safe_div(p_data['marks_scored'], p_data['total_marks']) * 100
        
        # Applying your explicit class logic to the final pool totals
        if p_data['overall_accuracy'] >= 70:
            p_data['accuracy_class'] = 'text-success'
        elif 40 < p_data['overall_accuracy'] < 70:
            p_data['accuracy_class'] = 'text-warning-emphasis'
        else:
            p_data['accuracy_class'] = 'text-danger'

        if p_data['score'] >= 70:
            p_data['score_class'] = 'text-success'
        elif 40 < p_data['score'] < 70:
            p_data['score_class'] = 'text-warning-emphasis'
        else:
            p_data['score_class'] = 'text-danger'

    # Enforce final sorting in Python
    for section_data in sections.values():
        section_data['questions'].sort(key=lambda x: getattr(x, 'display_order', float('inf')))


    perf['1m_accuracy'] = safe_div(perf['1m_correct'], perf['1m_attempts']) * 100
    perf['2m_accuracy'] = safe_div(perf['2m_correct'], perf['2m_attempts']) * 100
    perf['overall_accuracy'] = safe_div(perf['1m_correct'] + perf['2m_correct'], perf['total_attempts']) * 100

    perf['total_correct'] = perf['1m_correct'] + perf['2m_correct']
    perf['total_incorrect'] = perf['1m_incorrect'] + perf['2m_incorrect']
    perf['total_skipped'] = perf['1m_skipped'] + perf['2m_skipped']

    perf['1m_skipped_m'] = perf['1m_skipped']
    perf['2m_skipped_m'] = perf['2m_skipped'] * 2
    perf['total_skipped_m'] = perf['1m_skipped_m'] + perf['2m_skipped_m']

    perf['total_attempted_m'] = perf['1m_attempted_m'] + perf['2m_attempted_m']
    perf['total_correct_m'] = perf['1m_correct_m'] + perf['2m_correct_m']
    perf['total_penalty_m'] = perf['1m_penalty_m'] + perf['2m_penalty_m']
    
    perf['1m_resultant_m'] = perf['1m_correct_m'] - perf['1m_penalty_m']
    perf['2m_resultant_m'] = perf['2m_correct_m'] - perf['2m_penalty_m']
    perf['total_resultant_m'] = perf['1m_resultant_m'] + perf['2m_resultant_m']

    hist_rank = attempt.historical_rank or 0
    total_takes = exam.total_takes or 0
    perf['percentile'] = 100 - (safe_div(hist_rank, total_takes) * 100) if hist_rank and total_takes else 0
    perf['percentage'] = safe_div(total_marks_obtained, exam.total_marks) * 100

    avg_marks = exam.avg_marks or 0
    top_10 = exam.top_10_avg_marks or 0
    perf['diff_from_avg'] = total_marks_obtained - avg_marks
    perf['diff_from_top_10'] = total_marks_obtained - top_10
    perf['diff_from_topper'] = total_marks_obtained - (exam.highest_marks or 0)

    perf['avg_time_per_que'] = safe_div(attempt.time_taken_mins, perf['total_attempts'])
    
    try:
        perf['formatted_highest_time'] = time_seconds_to_mins_seconds(perf['highest_time_sec'])
    except NameError:
        perf['formatted_highest_time'] = f"{perf['highest_time_sec']}s"

    sections = {k: v for k, v in sections.items() if v['questions']}
    
    return perf, sections, total_marks_obtained, dict(subject_wise_break_down), dict(pooled_data)
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
    

def calculate_attempt_performance(exam, attempt, exam_questions, user_responses):
    sections = {
        'General Aptitude': {'questions': [], 'marks': 0}, 
        'Technical': {'questions': [], 'marks': 0}
    }
    total_marks_obtained = 0.0

    perf = {
        '1m_attempts': 0, '2m_attempts': 0, 'total_attempts': 0,
        '1m_correct': 0, '2m_correct': 0, '1m_incorrect': 0, '2m_incorrect': 0,
        '1m_skipped': 0, '2m_skipped': 0, '1m_total_q': 0, '2m_total_q': 0,
        '1m_attempted_m': 0, '2m_attempted_m': 0,
        '1m_correct_m': 0, '2m_correct_m': 0,
        '1m_penalty_m': 0.0, '2m_penalty_m': 0.0,
        'highest_time_sec': 0
    }

    for eq in exam_questions:
        q_id = eq.question.q_id
        resp = user_responses.get(q_id, {})

        eq.user_ans = resp.get('ans')
        eq.time_taken_sec = resp.get('time_sec', 0)
        
        # Assign order for Python sorting (Future shuffle proof)
        eq.display_order = resp.get('presented_order', eq.original_order or q_id)
        
        try:
            eq.formtted_time_taken = time_seconds_to_mins_seconds(eq.time_taken_sec)
        except NameError:
            eq.formtted_time_taken = f"{eq.time_taken_sec}s"

        perf['highest_time_sec'] = max(perf['highest_time_sec'], eq.time_taken_sec)

        marks_award = eq.question.marks_award
        marks_penalty = eq.question.marks_penalty 

        m_key = f"{int(marks_award)}m"
        perf[f'{m_key}_total_q'] += 1

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
            
            if eq.user_ans == eq.question.correct_answer:
                total_marks_obtained += marks_award
                perf[f'{m_key}_correct'] += 1
                perf[f'{m_key}_correct_m'] += marks_award
                eq.ans_status = 'Correct'
                eq.color_class = 'bg-success'
            else:
                total_marks_obtained -= marks_penalty
                perf[f'{m_key}_incorrect'] += 1
                perf[f'{m_key}_penalty_m'] += marks_penalty
                eq.ans_status = 'Incorrect'
                eq.color_class = 'bg-warning text-dark' if marks_penalty == 0 else 'bg-danger'
        else:
            perf[f'{m_key}_skipped'] += 1
            eq.ans_status = 'Skipped'

        if 'aptitude' in eq.question.category.lower():
            sections['General Aptitude']['questions'].append(eq)
            sections['General Aptitude']['marks'] += eq.question.marks_award
        else:
            sections['Technical']['questions'].append(eq)
            sections['Technical']['marks'] += eq.question.marks_award

    # Enforce final sorting in Python
    for section_data in sections.values():
        section_data['questions'].sort(key=lambda x: getattr(x, 'display_order', float('inf')))

    def safe_div(num, den):
        return (num / den) if den else 0

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
    
    return perf, sections, total_marks_obtained
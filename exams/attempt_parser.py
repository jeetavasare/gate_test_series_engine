import json
import re
from bs4 import BeautifulSoup
from django.db import transaction
from .models import Attempt, Exam, TestPackage

def process_attempts_upload(user, results_file, html_files):
    results_data = json.load(results_file)
    
    valid_db_exam_ids = set(Exam.objects.values_list('exam_id', flat=True))
    
    json_attempts_map = {}
    for obj in results_data:
        exam_id = int(obj.get('exam_id', 0))
        
        if exam_id not in valid_db_exam_ids:
            continue
            
        for res in obj.get('results', []):
            time_m = int(res.get('time_taken_mins', 0))
            json_attempts_map[(exam_id, time_m)] = {
                'rank': res.get('rank'),
                'submitted_at': res.get('submitted_at_utc', 'Unknown')
            }

    attempts_to_create = []
    skipped_files = 0

    for html_file in html_files:
        soup = BeautifulSoup(html_file.read(), 'html.parser')
        
        exam_link_el = soup.select_one('.exam_name h2 a')
        if not exam_link_el or not exam_link_el.has_attr('href'):
            print("exam link not present", exam_link_el)
            skipped_files += 1
            continue
            
        exam_id_match = re.search(r'/exam/(\d+)', exam_link_el['href'])
        if not exam_id_match:
            print("exam id not match", exam_id_match)
            skipped_files += 1
            continue
            
        exam_id = int(exam_id_match.group(1))

        if exam_id not in valid_db_exam_ids:
            print("exam not in valid exams", exam_id)
            skipped_files += 1
            continue

        min_taken_elem = soup.select_one('.exam_min_taken')
        total_time_mins = 0
        if min_taken_elem:
            time_match = re.search(r'(\d+)', min_taken_elem.get_text())
            total_time_mins = int(time_match.group(1)) if time_match else 0
        
        # --- ARRAY IMPLEMENTATION HERE ---
        responses = [] 
        for q_el in soup.select('.res_question'):
            sol_container = q_el.select_one('.res_solution')
            if not sol_container: continue

            discuss_link = sol_container.select_one('.res_discuss a')
            if not discuss_link or not discuss_link.has_attr('href'): continue
            
            q_id_match = re.search(r'(?:gateoverflow\.in/|\.\./|/)(\d+)', discuss_link['href'])
            if not q_id_match: continue
            q_id = int(q_id_match.group(1))

            your_ans_el = sol_container.select_one('.user_solution')
            ans = None
            if your_ans_el:
                ans_text = your_ans_el.get_text(strip=True)
                ans = re.sub(r'(?i)Your Answer:\s*', '', ans_text).upper()

            time_el = sol_container.select_one('.res_qs_time_taken')
            time_sec = 0
            if time_el:
                time_text = time_el.get_text(strip=True)
                min_match = re.search(r'(\d+)min', time_text)
                sec_match = re.search(r'(\d+)sec', time_text)
                
                mins = int(min_match.group(1)) if min_match else 0
                secs = int(sec_match.group(1)) if sec_match else 0
                time_sec = (mins * 60) + secs

            # Append as an object
            # responses.append({
            #     'q_id': q_id,
            #     'ans': ans,
            #     'time_sec': time_sec
            # })
            responses.append([q_id,ans,time_sec, 0])

        json_match = json_attempts_map.get((exam_id, total_time_mins))
        
        rank = json_match['rank'] if json_match else None
        submitted_at = json_match['submitted_at'] if json_match else "Unknown"

        attempts_to_create.append(Attempt(
            user=user,
            exam_id=exam_id,
            submitted_at=submitted_at,
            time_taken_mins=total_time_mins,
            historical_rank=rank,
            responses=json.dumps(responses) # Dumps array format
        ))

    with transaction.atomic():
        Attempt.objects.bulk_create(attempts_to_create)

    return {
        "success": True,
        "attempts_inserted": len(attempts_to_create),
        "skipped_files": skipped_files
    }


# can parse only single attempt per exam, and the latest one that's the limitation
# since we don't scan html files to do the mny attemtps for single exam thingy
# which is fine since for pyq i have single attempts any ways
def process_pyq_attempts_upload(user, results_file):
    result_data = json.load(results_file)

    try:
        pyq_package = TestPackage.objects.get(code__iexact='PYQ')
        valid_db_exam_ids = set(Exam.objects.filter(packages=pyq_package).values_list('exam_id', flat=True))
    except TestPackage.DoesNotExist:
        valid_db_exam_ids = set()

    skipped_exams = []
    skipped_due_to_no_results = 0
    attempts_to_create = []
    
    for attempt in result_data:
        exam_id = int(attempt.get('exam_id'))
        
        if exam_id not in valid_db_exam_ids:
            skipped_exams.append({"exam_id": exam_id})
            continue
            
        results_list = attempt.get('results')
        if not results_list:
            skipped_due_to_no_results += 1
            continue
            
        results = results_list[0]

        responses = []
        # Target the values of the dictionary to get the arrays of questions
        questions_dict = attempt.get('questions', {})
        for section_questions in questions_dict.values():
            for que in section_questions:
                q_id = int(que['link'].rstrip('/').split('/')[-1])
                answer = que.get('your_answer')
                time_taken_secs = int(que['time_taken'][:2]) * 60 + int(que['time_taken'][6:8])
                que_status = 0
                responses.append([q_id, answer, time_taken_secs, que_status])

        attempts_to_create.append(Attempt(
            user=user,
            exam_id=exam_id,
            submitted_at=results.get('submitted_at_utc'),
            time_taken_mins=results.get('time_taken_mins', 0),
            historical_rank=results.get('rank'),
            responses=json.dumps(responses)
        ))

    with transaction.atomic():
        Attempt.objects.bulk_create(attempts_to_create)
        
    print(skipped_exams, skipped_due_to_no_results)
    return {
        "success": True,
        "attempts_inserted": len(attempts_to_create),
        "skipped_files": len(skipped_exams) + skipped_due_to_no_results,
    }
        
        
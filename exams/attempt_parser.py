import json
import re
from bs4 import BeautifulSoup
from django.db import transaction
from .models import Attempt, Exam

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
            skipped_files += 1
            continue
            
        exam_id_match = re.search(r'/exam/(\d+)', exam_link_el['href'])
        if not exam_id_match:
            skipped_files += 1
            continue
            
        exam_id = int(exam_id_match.group(1))

        if exam_id not in valid_db_exam_ids:
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
            responses.append({
                'q_id': q_id,
                'ans': ans,
                'time_sec': time_sec
            })

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
import json
import re
from datetime import datetime
from django.db import transaction
from .models import TestPackage, Exam, Question, Topper2026, ExamTopper, ExamQuestion

def process_package_upload(package_code, package_name, access_page_file, results_file, access_list_file, cs_tests_file):
    access_page_data = json.load(access_page_file)
    results_data = json.load(results_file)
    access_list_data = json.load(access_list_file)
    cs_tests_data = json.load(cs_tests_file)

    # 1. Map Access Page
    access_page_map = {}
    for row in access_page_data:
        if len(row) < 3: continue
        title_raw, url, topics_raw = row[0], row[1], row[2]
        match = re.search(r'/exam/(\d+)', url)
        if match:
            exam_id = int(match.group(1))
            title = title_raw.replace('\u00A0', ' ').replace('\n', ' | ').strip()
            topics = topics_raw.replace('\u00A0', ' ').strip()
            access_page_map[exam_id] = {'title': title, 'topics': topics}

    # 2. Map Access List 4
    access_list_map = {}
    for obj in access_list_data:
        if 'id' not in obj: continue
        exam_id = int(obj['id'])
        created_str = obj.get('created', '')
        try:
            dt = datetime.strptime(created_str, "%B %d, %Y")
            iso_date = dt.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            iso_date = created_str

        # raw_takes = str(obj.get('total_takes', '0')).replace(',', '').strip()
        # try:
        #     total_takes_val = int(raw_takes)
        # except ValueError:
        #     total_takes_val = -1

        access_list_map[exam_id] = {
            'sec_exam_title': obj.get('name', ''),
            'created_date': iso_date,
        }

    # 3. Map GATE Mocks
    mocks_map = {}
    for obj in results_data:
        exam_id = int(obj['exam_id'])
        info = obj.get('exam_info', {})
        
        # Extract Heat Map Data
        heat_map_dict = {}
        for hm in obj.get('heat_map', []):
            href = hm.get('href', '')
            hm_match = re.search(r'\.\./(\d+)/', href)
            if hm_match:
                hm_q_id = int(hm_match.group(1))
                
                title_str = hm.get('original-title', '')
                
                # Regex for Question Order
                # Matches "Question: 9", "Question : 6", "Question  :  12", etc.
                order_match = re.search(r'Question\s*:\s*(\d+)', title_str)
                order_val = int(order_match.group(1)) if order_match else None
                
                # Regex for Accuracy
                acc_match = re.search(r'Accuracy:\s*(\d+)%', title_str)
                acc_val = int(acc_match.group(1)) if acc_match else None

                heat_map_dict[hm_q_id] = {
                    'original_order': order_val,
                    'accuracy_percent': acc_val,
                    'color': hm.get('style_background_color', '')
                }

        mocks_map[exam_id] = {
            'duration_mins': info.get('total_time_mins', 0),
            'total_marks': info.get('maximum_marks', 0),
            'total_questions': info.get('total_questions', 0),
            'avg_marks': info.get('avg._mark'),
            'top_10_avg_marks': info.get('avg._mark_of_top_10'),
            'highest_marks': info.get('highest_mark'),
            'toppers': obj.get('toppers', []),
            'heat_map': heat_map_dict,
            'total_takes': info.get('total_takes', 0),
        }

    # 4. Map CS Tests
    cs_tests_map = {int(obj['exam_id']): obj for obj in cs_tests_data}

    # Intersections
    valid_exam_ids = set(access_page_map.keys()).intersection(
        access_list_map.keys(), mocks_map.keys(), cs_tests_map.keys()
    )
    skipped_ids = set(access_page_map.keys()).union(access_list_map.keys(), mocks_map.keys(), cs_tests_map.keys()) - valid_exam_ids

    # Transaction Block
    with transaction.atomic():
        package, _ = TestPackage.objects.get_or_create(code=package_code, defaults={'name': package_name})

        exams_to_create = []
        questions_dict = {}
        exam_questions_to_create = []

        for eid in valid_exam_ids:
                
            # REMOVED package=package from here
            exam = Exam(
                exam_id=eid,
                title=access_page_map[eid]['title'],
                sec_exam_title=access_list_map[eid]['sec_exam_title'],
                topics=access_page_map[eid]['topics'],
                created_date=access_list_map[eid]['created_date'],
                duration_mins=mocks_map[eid]['duration_mins'],
                total_marks=mocks_map[eid]['total_marks'],
                total_questions=mocks_map[eid]['total_questions'],
                total_takes=mocks_map[eid].get('total_takes', 0),
                avg_marks=mocks_map[eid]['avg_marks'],
                top_10_avg_marks=mocks_map[eid]['top_10_avg_marks'],
                highest_marks=mocks_map[eid]['highest_marks']
            )
            exams_to_create.append(exam)

            for section in cs_tests_map[eid].get('section', []):
                for q in section.get('question', []):
                    q_id = int(q['post_id'])
                    
                    if q_id not in questions_dict:
                        questions_dict[q_id] = Question(
                            q_id=q_id,
                            q_type=q.get('type', ''),
                            category=q.get('category', ''),
                            tags=q.get('tags', ''),
                            question_html=q.get('text', ''),
                            correct_answer=str(q.get('answer', '')).upper(),
                            marks_award=float(q.get('award', 0)),
                            marks_penalty=float(q.get('penalty', 0))
                        )
                    
                    hm_data = mocks_map[eid]['heat_map'].get(q_id, {})
                    
                    exam_questions_to_create.append(ExamQuestion(
                        exam_id=eid,
                        question_id=q_id,
                        original_order=hm_data.get('original_order'),
                        accuracy_percent=hm_data.get('accuracy_percent'),
                        heat_map_color=hm_data.get('color', '')
                    ))

        # 1. Create the exams safely
        Exam.objects.bulk_create(exams_to_create, ignore_conflicts=True)
        
        # 2. Link the package to all valid exams (handles overlaps perfectly)
        exams_in_db = Exam.objects.filter(exam_id__in=valid_exam_ids)
        package.exams.add(*exams_in_db)

        # Create Questions and Junctions
        Question.objects.bulk_create(questions_dict.values(), ignore_conflicts=True)
        ExamQuestion.objects.bulk_create(exam_questions_to_create, ignore_conflicts=True)

        # Toppers
        toppers_dict = {}
        exam_toppers_to_create = []

        for eid in valid_exam_ids:
            for t_data in mocks_map[eid]['toppers']:
                profile_link = t_data.get('profile_link', '')
                username = profile_link.rstrip('/').split('/')[-1] if profile_link else t_data.get('name', 'unknown').replace(' ', '_')

                if username not in toppers_dict:
                    toppers_dict[username] = Topper2026(
                        username=username,
                        name=t_data.get('name', ''),
                        profile_link=profile_link
                    )

                exam_toppers_to_create.append(ExamTopper(
                    exam_id=eid,
                    topper_id=username,
                    marks=t_data.get('marks', 0),
                    time_taken_mins=t_data.get('time_taken', 0)
                ))

        Topper2026.objects.bulk_create(toppers_dict.values(), ignore_conflicts=True)
        ExamTopper.objects.bulk_create(exam_toppers_to_create, ignore_conflicts=True)

    return {
        "success": True,
        "exams_processed": len(valid_exam_ids),
        "questions_processed": len(questions_dict),
        "skipped_exam_ids": list(skipped_ids)
    }
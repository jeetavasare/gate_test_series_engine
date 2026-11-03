# views.py
from django.shortcuts import render, get_object_or_404, redirect

from django.contrib.auth.decorators import login_required
from exams.helper import time_mins_to_hour_mins, ques_status_map
import json
import random
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from exams.models import Exam, Question, ExamQuestion, Attempt
from .models import UserExamSession
from exams.config import interface_behavior
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from exams.config import candidate_photo_dir
from datetime import timedelta, UTC
from exams.helper import replace_question_image_link
from django.db import transaction

@login_required
def exam_prep(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id)
    formatted_duration = time_mins_to_hour_mins(exam.duration_mins)
    
    # Mocking context based on your snippet
    context = {
        'exam': exam,
        'formatted_duration': formatted_duration
    }
    return render(request, 'exam_interface/exam_prep.html', context)


def recalculate_aggregates(recording):
    """Rebuilds exam and section aggregates from the current question states."""
    exam_agg = {
        "answered": 0, "not_answered": 0, "not_visited": 0,
        "marked_for_review": 0, "answered_and_marked_for_review": 0
    }
    
    section_aggs = []
    
    for sec in recording['sections']:
        sec_agg = {
            "section_name": sec['section_name'],
        }
        # sec_agg = {
        #     "section_name": sec['section_name'],
        #     "answered": 0, "not_answered": 0, "not_visited": 0,
        #     "marked_for_review": 0, "answered_and_marked_for_review": 0
        # }
        
        # for q in sec['questions']:
        #     status = q['status']
        #     if status in sec_agg:
        #         sec_agg[status] += 1
        #         exam_agg[status] += 1
                
        section_aggs.append(sec_agg)
        
    recording['exam_aggregate'] = {}
    recording['section_aggregates'] = section_aggs
    return recording


def build_redirect_url(exam_session):
    if exam_session.exam_mode == "test":
        redirect_url = "/gate/quiz"
    elif exam_session.current_stage == "login":
        redirect_url = "/gate/login"
    elif exam_session.current_stage == "instructions":
        redirect_url = "/gate/instructions"
    elif exam_session.current_stage == "exam_started":
        redirect_url = "/gate/quiz"
    else:
        redirect_url = "/"
    return redirect_url

def ExamSessionValid(user_exam_session):
    if not user_exam_session:
        return False
    
    if user_exam_session.current_stage == "exam_ended":
        return False
    
    exam_duration = timedelta(
        minutes=user_exam_session.exam.duration_mins,
        seconds=user_exam_session.compensatory_time_secs
    )
   
    exam_end_time = user_exam_session.exam_start_time + exam_duration
    if timezone.now() > exam_end_time:
        user_exam_session.current_stage = 'exam_ended'
        user_exam_session.save()
        return False
    return True
    
    # check time exceeded

# --- API ENDPOINTS ---

@login_required
@require_http_methods(["GET"])
def check_active_session(request):
    session = UserExamSession.objects.filter(user=request.user).exclude(current_stage='exam_ended').first()
    if not ExamSessionValid(session):
        return JsonResponse({"active": False})
    
    return JsonResponse({
        "active": True,
        "exam_id": session.exam_id,
        "redirect_url": build_redirect_url(session),
        "mode": session.exam_mode
    })


@login_required
@require_http_methods(["POST"])
def init_session(request):
    data = json.loads(request.body)
    exam_id = data.get('exam_id')
    mode = data.get('mode') 
    behavior = data.get('behavior')
    
    # UserExamSession.objects.filter(user=request.user).delete()
    active_session_exists = UserExamSession.objects.filter(user=request.user).exclude(current_stage='exam_ended').exists()
    
    if active_session_exists:
        return JsonResponse({"error": "An active exam session is already in progress."}, status=400)
    
    exam = Exam.objects.get(exam_id=exam_id)
    config = interface_behavior.get(behavior, {})
    
    # Handle Time Logic
    if mode == 'test':
        session_start_time = None
        exam_start_time = timezone.now()
        current_stage = 'exam_started'
    else:
        # Parse ISO strings from <input type="datetime-local"> to timezone-aware objects
        raw_session_start_str = parse_datetime(data.get('session_start'))
        raw_exam_start_str = parse_datetime(data.get('exam_start'))
        tz_offset = int(data.get('tz_offset', 0))

        session_start_time = raw_session_start_str + timedelta(minutes=tz_offset)
        exam_start_time = raw_exam_start_str + timedelta(minutes=tz_offset)

        session_start_time = timezone.make_aware(session_start_time, UTC)
        exam_start_time = timezone.make_aware(exam_start_time, UTC)
        current_stage = 'login'

    # Build Sections
    eqs = ExamQuestion.objects.filter(exam=exam).select_related('question').order_by('original_order')
    sections_map = {}
    
    for eq in eqs:
        cat = "General Aptitude" if "Aptitude" in eq.question.category else "Technical"
        if cat not in sections_map:
            sections_map[cat] = []
        sections_map[cat].append({
            "q_id": eq.question.q_id,
            "status": "not_visited",
            "time_spent_secs": 0,
            "user_ans": None
        })
    
    sections_array = []
    for sec_name, qs in sections_map.items():
        if config.get('shuffle_qs', False):
            random.shuffle(qs)
        qs[0]['status'] = "not_answered"
        sections_array.append({
            "questions": qs,
            "active_question": qs[0]['q_id'],
            "section_name": sec_name
        })
        
    recording = {
        "current_section_index": 0,
        # "current_section_active_question": sections_array[0]['questions'][0]['q_id'] if sections_array else None,
        "sections": sections_array,
    }
    
    recording = recalculate_aggregates(recording)
    
    UserExamSession.objects.create(
        user=request.user,
        exam=exam,
        current_stage=current_stage,
        exam_mode=mode,
        session_start_time=session_start_time,
        exam_start_time=exam_start_time,
        interface_behavior=config,
        session_recording=recording
    )
    
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["GET"])
def get_session_context(request):
    session = UserExamSession.objects.filter(user=request.user).exclude(current_stage='exam_ended').select_related('exam').first()
    if not ExamSessionValid(session):
        # Redirect to login so context_fetcher.js will redirect
        return JsonResponse({"redirect_url": "/login"})
    
    redirect_url = build_redirect_url(session)

    base_data = {
        # below two for auto fill 
        'registration_number': request.user.registration_number,
        'dob': request.user.login_bd,
        
        "candidate_name": request.user.full_name,
        "exam_title": session.exam.display_title,
        "registration_number": request.user.registration_number,
        "candidate_profile_image_full_link": candidate_photo_dir  + "/" + str(request.user.candidate_photo) if request.user.candidate_photo else "",
        "redirect_url": redirect_url
    }
    
    if session.current_stage == 'login':
        base_data["session_start_time"] = session.session_start_time
        return JsonResponse(base_data)
        
    if session.current_stage == 'instructions':
        base_data["exam_start_time"] = session.exam_start_time
        return JsonResponse(base_data)
        
    if session.current_stage == 'exam_started':
        recording = session.session_recording
        
        # Calculate time left by summing consumed time
        total_consumed_secs = sum(
            q['time_spent_secs'] 
            for sec in recording['sections'] 
            for q in sec['questions']
        )
        time_left_secs = (session.exam.duration_mins * 60) - total_consumed_secs
        
        # Build the heavy question payload
        q_ids = [q['q_id'] for sec in recording['sections'] for q in sec['questions']]
        questions_db = Question.objects.filter(q_id__in=q_ids)
        q_map = {q.q_id: q for q in questions_db}
        
        type_mapping = {"Multiple Choice": "MCQ", "Multiple Select": "MSQ", "Numerical": "NAT"}
        
        # Attach HTML and Type to the recording structure for the frontend
        payload_sections = []
        for sec in recording['sections']:
            payload_qs = []
            for q_state in sec['questions']:
                q_obj = q_map.get(q_state['q_id'])
                if q_obj:
                    payload_qs.append({
                        **q_state,
                        "question_html": replace_question_image_link(q_obj.question_html),
                        "q_type": type_mapping.get(q_obj.q_type, q_obj.q_type),
                        "marks_award": q_obj.marks_award,
                        "marks_penalty": q_obj.marks_penalty
                    })
            
            payload_sections.append({
                "questions": payload_qs,
                "active_question": sec['active_question']
            })
            
        return JsonResponse({
            **base_data,
            "exam_title": session.exam.display_title,
            "duration_mins": session.exam.duration_mins,
            "exam_start_time": session.exam_start_time,
            "interface_behavior": session.interface_behavior,
            "session_recording": {
                "current_section_index": recording.get('current_section_index'),
                # "current_section_active_question": recording.get('current_section_active_question'),
                "exam_aggregate": recording.get('exam_aggregate'),
                "section_aggregates": recording.get('section_aggregates'),
                "sections": payload_sections
            }
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def login_session(request):
    data = json.loads(request.body)
    session = UserExamSession.objects.filter(user=request.user, current_stage='login').select_related('exam').first()
    if not session:
        return JsonResponse({"success": False, "error": "Invalid session"})
        
    # Validation
    if data.get('registration_number').lower() == request.user.registration_number.lower() and data.get('dob') == request.user.login_bd:

        if session.exam_mode == 'simulation':
            now = timezone.now()
            if now < session.session_start_time:
                time_diff = session.session_start_time - now
                total_seconds = int(time_diff.total_seconds())
                
                hours, remainder = divmod(total_seconds, 3600)
                minutes = remainder // 60
                if not hours and not minutes:
                    minutes = 1
                time_parts = []
                if hours > 0:
                    time_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
                if minutes > 0 or hours == 0:
                    time_parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
                    
                time_str = " ".join(time_parts)
                return JsonResponse({
                    "success": False, 
                    "error": f"You can login after {time_str}"
                })
            
            if not ExamSessionValid(session):
                return JsonResponse({"success":False, "error": "This Exam has session has ended."})

        session.current_stage = 'instructions'
        session.save()
        return JsonResponse({"success": True})
        
    return JsonResponse({"success": False, "error": "Invalid credentials"})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def start_session(request):
    session = UserExamSession.objects.filter(user=request.user).exclude(current_stage='exam_ended').first()
    if session and session.current_stage in ['login', 'instructions']:
        session.current_stage = 'exam_started'
        if not session.exam_start_time:
            session.exam_start_time = timezone.now()
        session.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def sync_session(request):
    batch = json.loads(request.body)
    session = UserExamSession.objects.filter(user=request.user, current_stage='exam_started').first()
    if not ExamSessionValid(session):
        return JsonResponse({"error": "exam_ended"}, status=403)
    if not session:
        return JsonResponse({"error": "No active session"}, status=400)

    now = timezone.now()
    recording = session.session_recording
    
    # 1. Build an O(1) lookup map for questions to avoid nested loops for time tracking
    q_map = {}
    for sec in recording.get('sections', []):
        for q in sec.get('questions', []):
            q_map[q['q_id']] = q

    # 2. Process Batch
    for item in batch:
        event_type = item[0]

        if event_type == "hb":
            if session.last_heartbeat:
                delta_secs = (now - session.last_heartbeat).total_seconds()
                if delta_secs > 25:
                    session.compensatory_time_secs += int(delta_secs)
            session.last_heartbeat = now
            
        elif event_type == "time_sync_q":
            q_id = item[1]
            time_spent = item[2]
            if q_id in q_map:
                current_time = q_map[q_id].get('time_spent_secs', 0)
                q_map[q_id]['time_spent_secs'] = current_time + time_spent
                
        else:
            # It is a state mutation: [pathArray, value]
            path = item[0]
            value = item[1]
            
            current = recording
            try:
                for key in path[:-1]:
                    current = current[key]
                current[path[-1]] = value
            except (KeyError, IndexError, TypeError):
                # If client sends a bad path, ignore it and process the rest of the batch
                continue

    # 3. Save - This is not based on timestamping if somehow opens two tabs one can overwrite other
    session.session_recording = recording
    session.save(update_fields=['session_recording', 'last_heartbeat', 'compensatory_time_secs'])
    
    return JsonResponse({"status": "ok"})

def process_and_save_attempt(session):
    exam = session.exam
    recording = session.session_recording
    now = timezone.now()

    eqs = ExamQuestion.objects.filter(exam=exam).select_related('question')
    q_dict = {
        eq.question.q_id: {
            'correct': eq.question.correct_answer,
            'award': float(eq.question.marks_award),
            'penalty': float(eq.question.marks_penalty)
        } for eq in eqs
    }

    total_marks = 0.0
    responses_array = []

    for sec in recording.get('sections', []):
        for q in sec.get('questions', []):
            q_id = q['q_id']
            ans = q.get('user_ans')

            if isinstance(ans, list):
                ans = ";".join(sorted(str(a) for a in ans))

            time_sec = q.get('time_spent_secs', 0)
            status_str = q.get('status', 'not_visited')
            status_int = ques_status_map.get(status_str, 0)
            
            responses_array.append([q_id, ans, time_sec, status_int])
            
            if q_id in q_dict:
                q_data = q_dict[q_id]
                if q_data['correct'] == 'X':
                    total_marks += q_data['award']
                elif ans: 
                    if ans == q_data['correct']:
                        total_marks += q_data['award']
                    else:
                        total_marks -= q_data['penalty']

    if session.exam_start_time:
        max_end_time = session.exam_start_time + timedelta(minutes=exam.duration_mins)
        effective_submit_time = min(now, max_end_time)
        
        time_taken_secs = (effective_submit_time - session.exam_start_time).total_seconds()
        time_taken_mins = int(time_taken_secs // 60)
    else:
        effective_submit_time = now
        time_taken_mins = 0

    with transaction.atomic():
        Attempt.objects.create(
            user=session.user,
            exam=exam,
            submitted_at=effective_submit_time.isoformat(),
            time_taken_mins=time_taken_mins,
            marks_obtained=round(total_marks, 2),
            exam_mode=session.exam_mode,
            session_start_time=session.session_start_time,
            exam_start_time=session.exam_start_time,
            compensatory_time_secs=session.compensatory_time_secs,
            responses=json.dumps(responses_array)
        )
        session.delete()

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_exam(request):
    session = UserExamSession.objects.filter(
        user=request.user, 
        current_stage='exam_started'
    ).first()
    
    if not ExamSessionValid(session):
        return JsonResponse({"error": "exam_ended"}, status=403)
        
    process_and_save_attempt(session)
    
    return JsonResponse({"success": "ok"}, status=200)

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def recover_stranded_sessions(request):
    stuck_sessions = UserExamSession.objects.filter(current_stage='exam_ended')
    
    count = 0
    for session in stuck_sessions:
        process_and_save_attempt(session)
        count += 1
        
    return JsonResponse({"status": "success", "recovered_count": count}, status=200)


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .test_series_parser import process_package_upload
from .models import TestPackage, Exam, User, Question, Attempt, ExamQuestion
import re
from django.conf import settings
from .helper import time_mins_to_hour_mins, calculate_attempt_performance, replace_question_image_link
from .attempt_parser import process_attempts_upload
from django.http import JsonResponse, HttpResponseNotFound
import json
from django.shortcuts import get_object_or_404
from .config import *
from django.db.models import Prefetch

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'exams/login.html', {'error': 'Invalid credentials'})
            
    return render(request, 'exams/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        
        # Basic validation
        if User.objects.filter(username=username).exists():
            return render(request, 'exams/register.html', {'error': 'Username already exists.'})
            
        # create_user automatically hashes the password thanks to our UserManager
        user = User.objects.create_user(username=username, password=password, full_name=full_name)
        login(request, user)
        return redirect('home')
        
    return render(request, 'exams/register.html')


@login_required(login_url='login')
def home_view(request):
    packages = TestPackage.objects.all()
    
    # Get selected package from query params, default to first available
    selected_package_id = request.COOKIES.get('selected_pkg_id')

    if selected_package_id:
        selected_package = packages.filter(package_id=selected_package_id).first()
    else:
        selected_package = packages.first()

    # Fetch exams for the selected package
    exams = Exam.objects.filter(packages=selected_package) if selected_package else []

    package_stats = {'twts': 0, 'swts' : 0, 'mock_tests': 0, 'misc' : 0, 'total_questions': 0, 'total_exams': 0}

    for exam in exams:
        q_count = exam.total_questions
        package_stats['total_exams'] += 1
        package_stats['total_questions'] += q_count
        if q_count <= 20:
            package_stats['twts'] += 1
        elif  25 <= q_count <= 30:
            package_stats['swts'] += 1
        elif "mock" in exam.title.lower():
            package_stats['mock_tests'] += 1
        else:
            package_stats['misc'] += 1


    
    context = {
        'packages': packages,
        'selected_package': selected_package,
        'exams': exams,
        'package_stats': package_stats,
    }
    return render(request, 'exams/home.html', context)

@staff_member_required(login_url='home')
def upload_package_view(request):
    context = {}
    if request.method == 'POST':
        package_code = request.POST.get('package_code')
        package_name = request.POST.get('package_name')
        
        access_page = request.FILES.get('access_page')
        results = request.FILES.get('results')
        access_list = request.FILES.get('access_list')
        cs_tests = request.FILES.get('cs_tests')

        if all([package_code, package_name, access_page, results, access_list, cs_tests]):
            try:
                result = process_package_upload(
                    package_code, package_name, 
                    access_page, results, access_list, cs_tests
                )
                context['result'] = result
            except Exception as e:
                context['error'] = f"Processing failed: {str(e)}"
        else:
            context['error'] = "All fields and files are required."
            
    return render(request, 'exams/upload_package.html', context)

@login_required(login_url='login')
def question_paper(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)
    exam_questions = exam.exam_questions.select_related('question').order_by('original_order', 'question__q_id')
    attempt = Attempt.objects.filter(exam=exam, user=request.user).first()

    if not attempt and not request.user.is_superuser:
        return HttpResponseNotFound("Resource not found")

    static_prefix = settings.STATIC_URL
    
    # Restructure dictionary to hold both questions and accumulated marks
    sections = {
        'General Aptitude': {'questions': [], 'marks': 0}, 
        'Technical': {'questions': [], 'marks': 0}
    }

    for eq in exam_questions:
        if 'gateoverflow_exam_images' in eq.question.question_html:
            eq.question.question_html = re.sub(
                r'src=["\'](gateoverflow_exam_images/[^"\']+)["\']', 
                rf'src="{static_prefix}\1"', 
                eq.question.question_html
            )
            
        # Group logic and accumulate marks
        if 'aptitude' in eq.question.category.lower():
            sections['General Aptitude']['questions'].append(eq)
            sections['General Aptitude']['marks'] += eq.question.marks_award
        else:
            sections['Technical']['questions'].append(eq)
            sections['Technical']['marks'] += eq.question.marks_award

    # Remove the Aptitude section entirely if it has no questions
    sections = {k: v for k, v in sections.items() if v['questions']}

    formatted_duration = time_mins_to_hour_mins(exam.duration_mins)

    return render(request, 'exams/question_paper.html', {'exam': exam, 'sections': sections, 'formatted_duration': formatted_duration})

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def exam_details_view(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)

    # 1. Fetch questions ONCE, deferring the heavy HTML payload to keep it instant
    exam_questions = exam.exam_questions.select_related('question')\
        .defer('question__question_html', 'question__tags')\
        .order_by('original_order', 'question__q_id')

    # Calculate stats
    stats = {'1m_count': 0, '2m_count': 0, '1m_marks': 0, '2m_marks': 0, 'apti_count': 0, 'tech_count': 0}
    
    for eq in exam_questions:
        award = eq.question.marks_award
        is_apti = 'aptitude' in eq.question.category.lower()

        if award == 1.0:
            stats['1m_count'] += 1
            stats['1m_marks'] += 1.0
        elif award == 2.0:
            stats['2m_count'] += 1
            stats['2m_marks'] += 2.0

        if is_apti:
            stats['apti_count'] += 1
        else:
            stats['tech_count'] += 1

    stats['sections'] = 2 if stats['apti_count'] > 0 else 1

    # Fetch toppers
    exam_toppers = exam.exam_toppers.all().select_related('topper').order_by('-marks', 'time_taken_mins')

    # 2. Fetch the user's specific attempts for this exam
    attempts = Attempt.objects.filter(exam=exam, user=request.user).order_by('-submitted_at')

    formatted_duration = time_mins_to_hour_mins(exam.duration_mins)
    
    context = {
        'exam': exam,
        'formatted_duration': formatted_duration,
        'exam_toppers': exam_toppers,
        'exam_questions': exam_questions, # Using the deferred query from the top
        'attempts': attempts,             # Passing the attempts to the template
        'stats': stats,
        'top_10_count': int(exam.total_takes / 10) if exam.total_takes else 0,
    }
    return render(request, 'exams/exam_details.html', context)

@staff_member_required(login_url='home')
def upload_attempts_view(request):
    users = User.objects.all()
    context = {'users': users}
    
    if request.method == 'POST':
        target_user_id = request.POST.get('user_id')
        results_json = request.FILES.get('results_json')
        html_files = request.FILES.getlist('html_files')
        
        if target_user_id and results_json and html_files:
            try:
                user = User.objects.get(user_id=target_user_id)
                result = process_attempts_upload(user, results_json, html_files)
                context['result'] = result
            except Exception as e:
                context['error'] = f"Processing failed: {str(e)}"
        else:
            context['error'] = "All fields and files are required."
            
    return render(request, 'exams/upload_attempts.html', context)


@login_required(login_url='login')
def get_question_text(request, q_id):
    try:
        # We only need the HTML field
        question = Question.objects.only('question_html', 'correct_answer').get(q_id=q_id)
        return JsonResponse({'success': True, 'html': question.question_html, 'correct_answer': question.correct_answer})
    except Question.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Question not found'}, status=404)
    

@login_required(login_url='login')
def results_view(request, attempt_id):
    attempt = get_object_or_404(Attempt, attempt_id=attempt_id)
    
    if attempt.user != request.user and not request.user.is_superuser:
        return HttpResponseNotFound("Resource not found")

    exam = attempt.exam
    
    # --- STRICT ARRAY PARSING LOGIC ---
    try:
        raw_responses = json.loads(attempt.responses) if attempt.responses else []
        user_responses = {}
        # Parse new array structure, capturing the index as the true order
        for idx, item in enumerate(raw_responses):
            q_id = int(item.get('q_id', 0))
            if q_id:
                user_responses[q_id] = {
                    'ans': item.get('ans'),
                    'time_sec': item.get('time_sec', 0),
                    'presented_order': idx + 1 # 1-based index
                }
    except json.JSONDecodeError:
        user_responses = {}

    exam_questions = list(exam.exam_questions.select_related('question').order_by('original_order', 'question__q_id'))

    static_prefix = settings.STATIC_URL

    for eq in exam_questions:
        if 'gateoverflow_exam_images' in eq.question.question_html:
            eq.question.question_html = re.sub(
                r'src=["\'](gateoverflow_exam_images/[^"\']+)["\']', 
                rf'src="{static_prefix}\1"', 
                eq.question.question_html
            )

    perf, sections, total_marks_obtained, subject_wise_break_down, pooled_data = calculate_attempt_performance(exam, attempt, exam_questions, user_responses)

    time_unutilised_mins = exam.duration_mins - (attempt.time_taken_mins or 0)
    try:
        formatted_total_duration = time_mins_to_hour_mins(exam.duration_mins)
        formatted_attempt_duration = time_mins_to_hour_mins(attempt.time_taken_mins or 0)
    except NameError:
        formatted_total_duration = f"{exam.duration_mins}m"
        formatted_attempt_duration = f"{attempt.time_taken_mins or 0}m"

    medal = ''
    medal_title = ''
    if perf['percentile'] >= 90:
        medal = '🏆'
        medal_title = "ACE - Enter top 10%"
    if total_marks_obtained > (exam.highest_marks or 0):
        medal = '🥇 🏆'
        medal_title = "CONQUEROR"

    context = {
        'attempt': attempt,
        'exam': exam,
        'sections': sections,
        'resultant_marks': total_marks_obtained,
        'formatted_total_duration': formatted_total_duration,
        'formatted_attempt_duration': formatted_attempt_duration,
        'perf': perf,
        'time_unutilised_mins': time_unutilised_mins,
        'medal': medal,
        'medal_title': medal_title,
        'subject_wise_break_down' : subject_wise_break_down,
        'pooled_data': pooled_data
    }
    
    return render(request, 'exams/results_view.html', context)
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

gate_interface = [
    path('login/', TemplateView.as_view(template_name='gate_exam_interface/login.html'), name='login'),
    path('instructions/', TemplateView.as_view(template_name='gate_exam_interface/instructions.html'), name='instructions'),
    path('quiz/', TemplateView.as_view(template_name='gate_exam_interface/quiz.html'), name='quiz'),
    path('feedback/', TemplateView.as_view(template_name='gate_exam_interface/feedback.html'), name='feedback'),
]


exam_interface_apis = [
    path('active/', views.check_active_session),
    path('init/', views.init_session),
    path('context/', views.get_session_context),
    path('login/', views.login_session),
    path('start/', views.start_session),
    path('sync/', views.sync_session),
    path('submit/', views.submit_exam),
]

urlpatterns = [
    path('gate/', include((gate_interface, 'exam'))),
    path('examprep/<int:exam_id>/', views.exam_prep, name='exam_prep'),

    path('recover-stranded-sessions/', views.recover_stranded_sessions, name='recover_stranded_sessions'),
    path('api/exam_interface/', include(exam_interface_apis)),
]
# exams/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload-package/', views.upload_package_view, name='upload_package'),
    path('question_paper/<int:exam_id>/', views.question_paper, name='question_paper'),
    path('exam/<int:exam_id>/', views.exam_details_view, name='exam_details'),
    path('register/', views.register_view, name='register'),
    path('upload-attempts/', views.upload_attempts_view, name='upload_attempts'),
    path('api/get-question-text/<int:q_id>/', views.get_question_text, name='get_question_text'),
    path('results/<int:attempt_id>/', views.results_view, name='results_view'),
]
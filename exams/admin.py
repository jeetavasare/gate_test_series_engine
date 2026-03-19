from django.contrib import admin
from .models import User, TestPackage, Exam, Question, Attempt

# Register your models here.
admin.site.register(User)
admin.site.register(TestPackage)
admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Attempt)
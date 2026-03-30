from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    # Removed registration_number from required arguments
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Users must have a username')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    candidate_photo = models.CharField(max_length=255, null=True, blank=True)

    birthdate = models.DateField(null=True, blank=True)

    # Required for Django admin/auth compatibility
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    # username is now the login field
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name']

    @property
    def login_bd(self):
        """Returns the birthdate in DDMMYYYY format for GATE mock test authentication."""
        if self.birthdate:
            return self.birthdate.strftime('%d%m%Y')
        return None

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
    
    def __str__(self):
        return self.username

class TestPackage(models.Model):
    package_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True) # e.g., CS26, DA26
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.code

class Exam(models.Model):
    exam_id = models.IntegerField(primary_key=True)
    # Replaced ForeignKey with ManyToManyField
    packages = models.ManyToManyField(TestPackage, related_name='exams')
    title = models.CharField(max_length=255)
    sec_exam_title = models.CharField(max_length=255, null=True, blank=True)
    topics = models.TextField(null=True, blank=True)
    created_date = models.CharField(max_length=50, null=True, blank=True)
    duration_mins = models.IntegerField()
    total_marks = models.FloatField()
    total_questions = models.IntegerField()
    total_takes = models.IntegerField() # comes from Gate_Mocks_17... .json.exam_info[total_takes]
    avg_marks = models.FloatField(null=True, blank=True)
    top_10_avg_marks = models.FloatField(null=True, blank=True)
    highest_marks = models.FloatField(null=True, blank=True)

    @property
    def display_title(self):
        return self.title.replace("GO Classes", "").replace("CS", "GATE CS").replace(" ", " ").strip()

    def __str__(self):
        return str(self.exam_id) + " " + self.title

class Question(models.Model):
    q_id = models.IntegerField(primary_key=True)
    # exam ForeignKey is REMOVED
    q_type = models.CharField(max_length=50)
    category = models.CharField(max_length=100)
    tags = models.TextField(null=True, blank=True)
    question_html = models.TextField()
    correct_answer = models.CharField(max_length=255)
    marks_award = models.FloatField()
    marks_penalty = models.FloatField()

    def __str__(self):
        return str(self.q_id) + ": " + self.category + " - " + self.q_type + "(" + str(self.marks_award) + ")"
    
class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_exams')
    original_order = models.IntegerField(null=True, blank=True)
    accuracy_percent = models.IntegerField(null=True, blank=True)
    heat_map_color = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('exam', 'question')


class Attempt(models.Model):
    attempt_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    # on del set null becuase don't want attempts to be wiped out by wiping exam or test packages packages
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, related_name='attempts')
    submitted_at = models.CharField(max_length=100)
    time_taken_mins = models.IntegerField(null=True, blank=True)
    historical_rank = models.IntegerField(null=True, blank=True) # picked from the results section of Gate_Mocks_17.. .json
    responses = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id} - {self.exam_id}"
    

class Topper2026(models.Model):
    username = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    profile_link = models.TextField()

    def __str__(self):
        return self.username

class ExamTopper(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_toppers')
    topper = models.ForeignKey(Topper2026, on_delete=models.CASCADE, related_name='topper_exams')
    marks = models.FloatField()
    time_taken_mins = models.IntegerField()

    class Meta:
        unique_together = ('exam', 'topper') # Prevents duplicate entries for the same exam
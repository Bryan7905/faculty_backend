from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, EvaluationSession, Evaluation, DHSession

# 1. Custom User Admin
# We use UserAdmin so we still get the nice password hashing/permissions UI
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Fields', {'fields': ('role', 'department')}),
    )
    list_display = ['username', 'email', 'role', 'department', 'is_staff']
    list_filter = ['role', 'department']

# 2. Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'faculty']
    search_fields = ['name', 'code']
    filter_horizontal = ['students'] # Makes selecting many students much easier

# 3. Evaluation Session Admin
@admin.register(EvaluationSession)
class EvaluationSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'start_date', 'end_date']

# 4. Evaluation Results (ReadOnly for integrity)
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['course', 'faculty', 'teaching_quality', 'created_at']
    readonly_fields = ['created_at']
    # You might want to make everything readonly here so admins can't "fix" scores

# 5. Security Sessions (Mostly for debugging)
@admin.register(DHSession)
class DHSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'created_at']
    readonly_fields = ['server_private_key', 'shared_secret']
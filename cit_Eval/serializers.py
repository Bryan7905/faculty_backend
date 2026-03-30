from rest_framework import serializers
from .models import User, Course, Evaluation, EvaluationSession

# 1. User Serializer (To show who is who)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'department', 'first_name', 'last_name']

# 2. Course Serializer (To show students which courses they need to evaluate)
class CourseSerializer(serializers.ModelSerializer):
    faculty_name = serializers.ReadOnlyField(source='faculty.get_full_name')

    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'faculty', 'faculty_name']

# 3. Evaluation Submission Serializer (The most important one)
class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            'course', 
            'faculty', 
            'teaching_quality', 
            'punctuality', 
            'course_content', 
            'comments'
        ]

    # Validation: Ensure ratings are between 1 and 5
    def validate_teaching_quality(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

# 4. Analytics Serializer (For the Faculty/Admin Dashboard)
class FacultyPerformanceSerializer(serializers.Serializer):
    """
    This is a 'Plain' Serializer (not linked to one model) 
    used to send aggregated data like averages to React.
    """
    avg_quality = serializers.FloatField()
    avg_punctuality = serializers.FloatField()
    total_responses = serializers.IntegerField()
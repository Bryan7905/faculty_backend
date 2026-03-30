from rest_framework import serializers
from .models import User, Course, Evaluation

class CourseSerializer(serializers.ModelSerializer):
    faculty_name = serializers.ReadOnlyField(source="faculty.get_full_name")

    class Meta:
        model = Course
        fields = ["id", "name", "code", "faculty", "faculty_name"]

    def validate_faculty(self, value: User):
        if value.role != "faculty":
            raise serializers.ValidationError("Course faculty must have role='faculty'.")
        return value

class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ["course", "faculty", "teaching_quality", "punctuality", "course_content", "comments"]

    def validate(self, attrs):
        course = attrs.get("course")
        faculty = attrs.get("faculty")
        if course and faculty and course.faculty_id != faculty.id:
            raise serializers.ValidationError({"faculty": "Faculty must match the course faculty."})
        return attrs

    def _validate_rating(self, value, field_name):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(f"{field_name} must be between 1 and 5.")
        return value

    def validate_teaching_quality(self, value):
        return self._validate_rating(value, "teaching_quality")

    def validate_punctuality(self, value):
        return self._validate_rating(value, "punctuality")

    def validate_course_content(self, value):
        return self._validate_rating(value, "course_content")
from django.urls import path
from .views import DiffieHellmanHandshakeView, EvaluationSubmitView, CourseListView

urlpatterns = [
    # The Security Handshake
    path('dh/handshake/', DiffieHellmanHandshakeView.as_view(), name='dh-handshake'),
    
    # Academic Data
    path('courses/', CourseListView.as_view(), name='course-list'),
    
    # Evaluation Submission
    path('submit-evaluation/', EvaluationSubmitView.as_view(), name='submit-eval'),
]
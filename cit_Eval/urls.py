from django.urls import path
from .views import DiffieHellmanHandshakeView, EvaluationSubmitView, CourseListView

urlpatterns = [
    path('dh/handshake/', DiffieHellmanHandshakeView.as_view()),
    path('courses/', CourseListView.as_view()),
    #path('courses/<int:pk>/', CourseDetailView.as_view()), # <--- New route for PUT/DELETE
    path('submit-evaluation/', EvaluationSubmitView.as_view()),
]
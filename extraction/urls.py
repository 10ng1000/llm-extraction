from django.urls import path
from . import views

urlpatterns = [
    path('projects/<int:project_id>/', views.ProjectView.as_view(), name='project'),
    path('projects/<int:project_id>/outputs/', views.OutputView.as_view(), name='output'),
    path('projects/<int:project_id>/tasks/', views.TaskView.as_view(), name='task'),
    path('projects/<int:project_id>/doccano/', views.DoccanoView.as_view(), name='docccano')
]
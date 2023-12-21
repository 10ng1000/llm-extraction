from django.urls import path
from . import views

urlpatterns = [
    path('import_data', views.ImportData.as_view(), name='import_data'),
    path('execute_extraction', views.ExecuteExtraction.as_view(), name='execute_extraction'),
    path('revoke_task', views.RevokeTask.as_view(), name='cancle_task'),
    path('get_output/', views.GetOutput.as_view(), name='get_output'),
    path('get_task_status/', views.GetTaskStatus.as_view(), name='get_task_status'),
    path('reset', views.Reset.as_view(), name='reset'),
    path('to_doccano', views.ToDoccano.as_view(), name='to_docccano'),
    path('get_doccano_status/', views.GetDoccanoStatus.as_view(), name='get_doccano_status')
]
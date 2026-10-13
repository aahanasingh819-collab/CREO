from django.urls import path
from . import views
from discovery import comparison
urlpatterns = [path('', views.directory, name='directory'), path('edit/', views.edit_profile, name='profile_edit'),
               path('compare/', comparison.compare, name='creator_compare'),
               path('<int:pk>/compare/', comparison.update, name='comparison_update'),
               path('<int:pk>/', views.detail, name='creator_detail')]

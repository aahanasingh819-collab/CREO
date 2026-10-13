from django.urls import path
from . import views
urlpatterns = [path('new/', views.edit, name='portfolio_create'), path('<int:pk>/', views.detail, name='portfolio_detail'), path('<int:pk>/edit/', views.edit, name='portfolio_edit'), path('<int:pk>/delete/', views.delete, name='portfolio_delete')]

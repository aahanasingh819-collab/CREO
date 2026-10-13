from django.urls import path
from . import views
urlpatterns = [path('', views.inbox, name='engagement_inbox'), path('<int:pk>/', views.detail, name='engagement_detail'),
               path('invite/<int:brief_pk>/<int:creator_pk>/', views.invite, name='invite_creator')]

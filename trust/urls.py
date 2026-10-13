from django.urls import path
from . import views
urlpatterns = [path('', views.mine, name='evidence_list'), path('project/<int:pk>/new/', views.submit, name='evidence_submit'),
               path('<int:pk>/file/', views.file, name='evidence_file'), path('<int:pk>/withdraw/', views.withdraw, name='evidence_withdraw'),
               path('review/', views.queue, name='review_queue'), path('review/<int:pk>/', views.review, name='evidence_review')]

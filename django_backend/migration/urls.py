from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user),
    path('signin/', views.signin_user),
    path('connect-zoho/', views.connect_zoho),
    path('receive-customers/', views.receive_customers),
    path('next-task/', views.get_next_task),
]
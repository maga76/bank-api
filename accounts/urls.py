from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
]

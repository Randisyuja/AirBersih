from django.urls import path
from users.views import (Dashboard, get_layanan_by_rumah, UserLoginView, UserLogoutView, SignUpView)

urlpatterns = [
    path('', Dashboard.as_view(), name='dashboard'),
    path("get-layanan/", get_layanan_by_rumah, name="get_layanan_by_rumah"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
]

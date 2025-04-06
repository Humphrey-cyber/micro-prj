from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import stk_push
from django.contrib.auth import views as auth_views
from .views import account_status
from .views import payout

urlpatterns = [
    path('home', views.home, name='home'),
    path('investments/', views.investments, name='investments'),
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('investment/<int:id>/', views.investment_detail, name='investment_detail'),
    path("stk_push/", stk_push, name="stk_push"),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('account-status/', account_status, name='account_status'),
    path('payout/', payout, name='payout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
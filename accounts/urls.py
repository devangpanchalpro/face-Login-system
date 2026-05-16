from django.urls import path
from . import views

urlpatterns = [
    # Page routes
    path('', views.home_page, name='home_page'),
    path('register/', views.register_page, name='register_page'),
    path('login/', views.login_page, name='login_page'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('logout/', views.logout_view, name='logout'),

    # API routes
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/login-history/<int:user_id>/', views.api_login_history, name='api_login_history'),
]

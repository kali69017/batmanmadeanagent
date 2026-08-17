from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard", views.dashboard, name="dashboard_alias"),
    path("onboarding", views.onboarding_view, name="onboarding"),
    path("onboarding/complete", views.onboarding_complete, name="onboarding_complete"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("scan", views.admin_scan_view, name="admin_scan"),
    path("api/positions", views.positions_view, name="api_positions"),
    path("api/today-signals", views.today_signals_view, name="api_today_signals"),
    path("api/portfolio-summary", views.portfolio_summary_view, name="api_portfolio_summary"),
    path("api/scan-stream", views.scan_stream, name="api_scan_stream"),
    path("api/chat-stream", views.chat_stream, name="api_chat_stream"),
    path("api/chat-sessions", views.chat_sessions_view, name="api_chat_sessions"),
    path("api/chat-sessions/<str:session_key>/messages", views.chat_session_detail, name="api_chat_session_detail"),
    path("api/chat-sessions/<str:session_key>/delete", views.chat_session_delete, name="api_chat_session_delete"),
    path("api/new-chat", views.new_chat_session, name="api_new_chat"),
    path("api/reset-chat", views.reset_chat_view, name="api_reset_chat"),
    path("api/health", views.health_view, name="api_health"),
]

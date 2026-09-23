from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("mis-fotos/", views.dashboard, name="dashboard"),
    path(
        "mis-fotos/login/",
        auth_views.LoginView.as_view(
            template_name="website/dashboard_login.html",
            redirect_authenticated_user=True,
        ),
        name="dashboard_login",
    ),
    path(
        "mis-fotos/salir/",
        auth_views.LogoutView.as_view(next_page="dashboard_login"),
        name="dashboard_logout",
    ),
    path("mis-fotos/<int:pk>/actualizar/", views.dashboard_update, name="dashboard_update"),
    path("mis-fotos/<int:pk>/eliminar/", views.dashboard_delete, name="dashboard_delete"),
]

from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("mis-fotos/", views.dashboard, name="dashboard"),
    path(
        "mis-fotos/login/",
        never_cache(
            views.RateLimitedLoginView.as_view(
                template_name="website/dashboard_login.html",
                redirect_authenticated_user=True,
            )
        ),
        name="dashboard_login",
    ),
    path(
        "mis-fotos/salir/",
        auth_views.LogoutView.as_view(next_page="dashboard_login"),
        name="dashboard_logout",
    ),
    path("mis-fotos/lista/", views.dashboard_list, name="dashboard_list"),
    path("mis-fotos/api/slot/<slug:slot>/upload/", views.api_slot_upload, name="api_slot_upload"),
    path("mis-fotos/api/gallery/upload/", views.api_gallery_upload, name="api_gallery_upload"),
    path("mis-fotos/api/gallery/reorder/", views.api_gallery_reorder, name="api_gallery_reorder"),
    path("mis-fotos/api/texts/", views.api_texts_save, name="api_texts_save"),
    path("mis-fotos/api/move/", views.api_move, name="api_move"),
    path("mis-fotos/api/photo/<int:pk>/delete/", views.api_photo_delete, name="api_photo_delete"),
    path("mis-fotos/<int:pk>/actualizar/", views.dashboard_update, name="dashboard_update"),
    path("mis-fotos/<int:pk>/eliminar/", views.dashboard_delete, name="dashboard_delete"),
    # Nuevas rutas integradas para el carrusel multimedia y panel de personalización
    path("mis-fotos/api/carousel/add/", views.editor_carousel_add, name="editor_carousel_add"),
    path("mis-fotos/api/carousel/reorder/", views.editor_carousel_reorder, name="editor_carousel_reorder"),
    path("mis-fotos/api/carousel/<int:pk>/toggle/", views.editor_carousel_toggle, name="editor_carousel_toggle"),
    path("mis-fotos/api/carousel/<int:pk>/delete/", views.editor_carousel_delete, name="editor_carousel_delete"),
    path("mis-fotos/api/settings/save/", views.editor_settings_save, name="editor_settings_save"),
]
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("leads/new/", views.lead_create, name="lead-create"),
    path("leads/import/", views.lead_import, name="lead-import"),
    path("leads/<int:pk>/", views.lead_detail, name="lead-detail"),
    path("leads/<int:pk>/update/", views.lead_update, name="lead-update"),
]

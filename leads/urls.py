from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.lead_list, name="list"),
    path("new/", views.lead_create, name="create"),
    path("route/", views.lead_route, name="route"),
    path("route/by-location/", views.lead_route_by_location, name="route_by_location"),
    path("<int:pk>/", views.lead_detail, name="detail"),
    path("<int:pk>/fetch-hours/", views.lead_fetch_hours, name="fetch_hours"),
    path("<int:pk>/delete/", views.lead_delete, name="delete"),
]

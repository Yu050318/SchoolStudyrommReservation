from django.urls import path

from . import views


urlpatterns = [
    path("health", views.health),
    path("auth/login", views.login),
    path("auth/register", views.register),
    path("rooms", views.rooms),
    path("rooms/<str:room_id>/seats", views.room_seats),
    path("bookings", views.create_booking),
    path("bookings/<int:user_id>", views.user_bookings),
    path("bookings/<int:booking_id>/status", views.booking_status),
    path("violations/<int:user_id>", views.user_violations),
    path("violations/<int:violation_id>/appeal", views.appeal_violation),
    path("admin/stats", views.admin_stats),
    path("admin/bookings", views.admin_bookings),
    path("admin/bookings/<int:booking_id>/status", views.admin_booking_status),
    path("admin/users", views.admin_users),
    path("admin/users/<int:user_id>", views.admin_user_detail),
    path("admin/violations", views.admin_violations),
    path("admin/violations/<int:violation_id>/status", views.admin_violation_status),
    path("admin/seats", views.admin_seats),
    path("admin/seats/<int:seat_id>/status", views.admin_seat_status),
    path("admin/rooms", views.admin_rooms),
    path("admin/rooms/<str:room_id>", views.admin_room_detail),
]

from django.contrib import admin

from .models import Booking, Room, Seat, User, Violation


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("account", "name", "role", "college", "class_name", "created_at")
    list_filter = ("role", "college")
    search_fields = ("account", "name", "college", "class_name")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "open_hours", "sort_order")
    search_fields = ("id", "name", "location")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("room", "seat_no", "status", "position_note", "config")
    list_filter = ("room", "status")
    search_fields = ("seat_no", "position_note", "config")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "room", "seat", "start_time", "end_time", "status", "created_at")
    list_filter = ("status", "room")
    search_fields = ("user__account", "user__name", "room__name", "seat__seat_no")


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "status", "happened_at")
    list_filter = ("type", "status")
    search_fields = ("user__account", "user__name", "type", "reason")

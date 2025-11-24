from django.contrib import admin
from .models import (
    Branch,
    BranchWorkHour,
    Service,
    Patient,
    Doctor,
    DoctorSchedule,
    PatientDocument,
    Appointment,
)


class BranchWorkHourInline(admin.TabularInline):
    model = BranchWorkHour
    extra = 0


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "phone_main", "is_active", "sort_order")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city", "address", "phone_main")
    ordering = ("sort_order", "name")
    prepopulated_fields = {"code": ("name",)}
    inlines = [BranchWorkHourInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_min", "price_from", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


class PatientDocumentInline(admin.TabularInline):
    model = PatientDocument
    extra = 0


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "branch", "age", "created_at")
    list_filter = ("branch",)
    search_fields = ("full_name", "phone", "email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PatientDocumentInline]


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 0


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "branch", "phone", "is_active")
    list_filter = ("branch", "is_active")
    search_fields = ("full_name", "specialization", "phone")
    inlines = [DoctorScheduleInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "branch",
        "doctor",
        "service",
        "date",
        "time",
        "status",
        "source",
        "is_first_visit",
        "created_at",
    )
    list_filter = (
        "branch",
        "doctor",
        "service",
        "status",
        "source",
        "is_first_visit",
        "date",
    )
    search_fields = ("full_name", "phone", "note", "internal_comment")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50
    list_editable = ("status",)

    fieldsets = (
        ("Основна інформація", {
            "fields": (
                "branch",
                "doctor",
                "service",
                ("date", "time"),
                "status",
            )
        }),
        ("Пацієнт", {
            "fields": (
                "patient",
                "full_name",
                "phone",
                "is_first_visit",
            )
        }),
        ("Деталі та коментарі", {
            "fields": (
                "note",
                "internal_comment",
                "source",
            )
        }),
        ("Системна інформація", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )

    actions = ["mark_confirmed", "mark_completed", "mark_cancelled"]

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status=Appointment.Status.CONFIRMED)
        self.message_user(request, f"Позначено як підтверджено: {updated} запис(ів).")
    mark_confirmed.short_description = "Позначити як підтверджені"

    def mark_completed(self, request, queryset):
        updated = queryset.update(status=Appointment.Status.COMPLETED)
        self.message_user(request, f"Позначено як завершено: {updated} запис(ів).")
    mark_completed.short_description = "Позначити як завершені"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=Appointment.Status.CANCELLED)
        self.message_user(request, f"Позначено як скасовано: {updated} запис(ів).")
    mark_cancelled.short_description = "Позначити як скасовані"

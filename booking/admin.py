from django.contrib import admin
from .models import (
    Branch,
    BranchWorkHour,
    Service,
    Patient,
    Doctor,
    DoctorSchedule,      # тижневий графік
    DoctorDaySchedule,   # денний override
    PatientDocument,
    Appointment,
    TreatmentCategory,
)

# =========================
# ФІЛІАЛИ + ГОДИНИ РОБОТИ
# =========================

class BranchWorkHourInline(admin.TabularInline):
    """
    Години роботи філіалу (по днях тижня) у картці філіалу.
    """
    model = BranchWorkHour
    extra = 0
    fields = ("weekday", "opens_at", "closes_at", "is_closed")
    ordering = ("weekday",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "phone_main", "is_active", "sort_order")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city", "address", "phone_main")
    ordering = ("sort_order", "name")
    prepopulated_fields = {"code": ("name",)}
    inlines = [BranchWorkHourInline]


# =========================
# ПОСЛУГИ
# =========================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_min", "price_from", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


# =========================
# ПАЦІЄНТИ + ДОКУМЕНТИ
# =========================

class PatientDocumentInline(admin.TabularInline):
    """
    Документи пацієнта прямо в картці пацієнта.
    """
    model = PatientDocument
    extra = 0
    fields = ("title", "file", "description", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "branch", "age", "created_at")
    list_filter = ("branch",)
    search_fields = ("full_name", "phone", "email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PatientDocumentInline]
    ordering = ("full_name",)
    autocomplete_fields = ("branch",)


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    """
    Окремий розділ для документів, якщо потрібно шукати/фільтрувати глобально.
    """
    list_display = ("title", "patient", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "patient__full_name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# =========================
# ЛІКАРІ + РОЗКЛАД
# =========================

class DoctorWeeklyScheduleInline(admin.TabularInline):
    """
    Тижневий графік (DoctorSchedule) в картці лікаря.
    Один рядок = день тижня + філіал.
    """
    model = DoctorSchedule
    extra = 0
    fields = ("branch", "weekday", "start_time", "end_time", "is_active")
    ordering = ("branch", "weekday")
    autocomplete_fields = ("branch",)


class DoctorDayScheduleInline(admin.TabularInline):
    """
    Денний override-графік (DoctorDaySchedule) в картці лікаря.
    Конкретні дати: відпустка, скорочений день, додаткові години тощо.
    """
    model = DoctorDaySchedule
    extra = 0
    fields = ("branch", "date", "start_time", "end_time", "is_working", "note")
    ordering = ("-date",)
    autocomplete_fields = ("branch",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialization", "branch", "phone", "is_active")
    list_filter = ("branch", "is_active", "specialization")
    search_fields = ("full_name", "specialization", "phone")
    ordering = ("full_name",)
    autocomplete_fields = ("branch", "user")
    inlines = [DoctorWeeklyScheduleInline, DoctorDayScheduleInline]


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    """
    Окремий розділ для тижневих графіків (шаблони по днях тижня).
    Зручно масово переглядати/редагувати.
    """
    list_display = ("doctor", "branch", "weekday", "start_time", "end_time", "is_active")
    list_filter = ("branch", "weekday", "is_active")
    search_fields = ("doctor__full_name", "branch__name")
    ordering = ("doctor", "branch", "weekday")
    autocomplete_fields = ("doctor", "branch")


@admin.register(DoctorDaySchedule)
class DoctorDayScheduleAdmin(admin.ModelAdmin):
    """
    Окремий розділ для денних override-графіків (конкретні дати).
    """
    list_display = ("date", "doctor", "branch", "start_time", "end_time", "is_working", "note")
    list_filter = ("branch", "doctor", "is_working", "date")
    search_fields = ("doctor__full_name", "branch__name", "note")
    date_hierarchy = "date"
    ordering = ("-date", "doctor")
    autocomplete_fields = ("doctor", "branch")


# =========================
# ЗАПИСИ НА ПРИЙОМ
# =========================

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
    ordering = ("-date", "-time")

    autocomplete_fields = ("branch", "doctor", "service", "patient")

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





@admin.register(TreatmentCategory)
class TreatmentCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "short_description", "full_description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("services",)
    ordering = ("sort_order", "-created_at")
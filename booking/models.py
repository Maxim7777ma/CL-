from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


class Branch(models.Model):
    """
    Філіал клініки.
    """
    name = models.CharField("Назва філії", max_length=255)
    code = models.SlugField(
        "Код (slug)",
        max_length=50,
        unique=True,
        help_text="Коротке імʼя для URL, наприклад: 'center', 'left-bank'"
    )
    city = models.CharField("Місто", max_length=100, default="Дніпро")
    address = models.CharField("Адреса", max_length=255)
    phone_main = models.CharField("Основний телефон", max_length=50, blank=True)
    phone_additional = models.CharField("Додатковий телефон", max_length=50, blank=True)
    email = models.EmailField("E-mail", blank=True)

    # Для карти
    latitude = models.DecimalField(
        "Широта (lat)",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Наприклад: 48.463020"
    )
    longitude = models.DecimalField(
        "Довгота (lng)",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Наприклад: 35.045727"
    )
    map_link = models.URLField(
        "Посилання на карту (Google/Apple)",
        blank=True,
        help_text="https://maps.google.com/..."
    )

    is_active = models.BooleanField("Активний філіал", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортування", default=10)

    class Meta:
        verbose_name = "Філіал"
        verbose_name_plural = "Філіали"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} — {self.city}"


class BranchWorkHour(models.Model):
    """
    Години роботи філіалу по дням тижня.
    """
    class WeekDay(models.IntegerChoices):
        MONDAY = 0, "Понеділок"
        TUESDAY = 1, "Вівторок"
        WEDNESDAY = 2, "Середа"
        THURSDAY = 3, "Четвер"
        FRIDAY = 4, "Пʼятниця"
        SATURDAY = 5, "Субота"
        SUNDAY = 6, "Неділя"

    branch = models.ForeignKey(
        Branch,
        verbose_name="Філіал",
        on_delete=models.CASCADE,
        related_name="work_hours",
    )
    weekday = models.IntegerField(
        "День тижня",
        choices=WeekDay.choices
    )
    opens_at = models.TimeField("Початок роботи", null=True, blank=True)
    closes_at = models.TimeField("Кінець роботи", null=True, blank=True)
    is_closed = models.BooleanField("Вихідний", default=False)

    class Meta:
        verbose_name = "Години роботи"
        verbose_name_plural = "Години роботи"
        unique_together = ("branch", "weekday")
        ordering = ["branch", "weekday"]

    def __str__(self):
        return f"{self.branch.name} — {self.get_weekday_display()}"


class Service(models.Model):
    """
    Стоматологічна послуга.
    """
    name = models.CharField("Назва послуги", max_length=200)
    description = models.TextField("Опис", blank=True)
    duration_min = models.PositiveIntegerField(
        "Тривалість (хвилин)",
        default=30,
        help_text="Скільки хвилин триває прийом"
    )
    price_from = models.DecimalField(
        "Ціна від",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField("Активна послуга", default=True)

    class Meta:
        verbose_name = "Послуга"
        verbose_name_plural = "Послуги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Patient(models.Model):
    """
    Пацієнт (клієнт). Може мати акаунт для входу на сайт.
    """
    user = models.OneToOneField(
        User,
        verbose_name="Користувач",
        related_name="patient_profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Опціонально: якщо у пацієнта є логін на сайті"
    )
    full_name = models.CharField("ПІБ", max_length=255)
    date_of_birth = models.DateField("Дата народження", null=True, blank=True)
    phone = models.CharField("Телефон", max_length=30)
    email = models.EmailField("E-mail", blank=True)
    branch = models.ForeignKey(
        Branch,
        verbose_name="Основний філіал",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patients"
    )

    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Пацієнт"
        verbose_name_plural = "Пацієнти"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years


class Doctor(models.Model):
    """
    Лікар (доктор). Використовуємо звʼязок з User для входу як адмін/лікар.
    """
    user = models.OneToOneField(
        User,
        verbose_name="Користувач",
        related_name="doctor_profile",
        on_delete=models.CASCADE,
        help_text="Акаунт лікаря для входу в систему"
    )
    full_name = models.CharField("ПІБ лікаря", max_length=255)
    specialization = models.CharField("Спеціалізація", max_length=255, blank=True)
    branch = models.ForeignKey(
        Branch,
        verbose_name="Основний філіал",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors"
    )
    room = models.CharField("Кабінет", max_length=50, blank=True)
    phone = models.CharField("Робочий телефон", max_length=30, blank=True)
    is_active = models.BooleanField("Активний лікар", default=True)

    class Meta:
        verbose_name = "Лікар"
        verbose_name_plural = "Лікарі"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class DoctorSchedule(models.Model):
    """
    Графік роботи лікаря по дням тижня.
    """
    class WeekDay(models.IntegerChoices):
        MONDAY = 0, "Понеділок"
        TUESDAY = 1, "Вівторок"
        WEDNESDAY = 2, "Середа"
        THURSDAY = 3, "Четвер"
        FRIDAY = 4, "Пʼятниця"
        SATURDAY = 5, "Субота"
        SUNDAY = 6, "Неділя"

    doctor = models.ForeignKey(
        Doctor,
        verbose_name="Лікар",
        on_delete=models.CASCADE,
        related_name="schedules"
    )
    branch = models.ForeignKey(
        Branch,
        verbose_name="Філіал",
        on_delete=models.CASCADE,
        related_name="doctor_schedules"
    )
    weekday = models.IntegerField(
        "День тижня",
        choices=WeekDay.choices
    )
    start_time = models.TimeField("Початок прийому")
    end_time = models.TimeField("Кінець прийому")
    is_active = models.BooleanField("Працює в цей день", default=True)

    class Meta:
        verbose_name = "Графік лікаря"
        verbose_name_plural = "Графік лікарів"
        unique_together = ("doctor", "weekday", "branch")
        ordering = ["doctor", "weekday"]

    def __str__(self):
        return f"{self.doctor.full_name} — {self.get_weekday_display()} ({self.branch.name})"


class PatientDocument(models.Model):
    """
    Документи пацієнта (аналізи, виписки, файли).
    """
    patient = models.ForeignKey(
        Patient,
        verbose_name="Пацієнт",
        on_delete=models.CASCADE,
        related_name="documents"
    )
    uploaded_by = models.ForeignKey(
        User,
        verbose_name="Хто завантажив",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_patient_documents"
    )
    title = models.CharField("Назва документа", max_length=255)
    file = models.FileField("Файл", upload_to="patient_docs/%Y/%m/")
    description = models.TextField("Опис", blank=True)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        verbose_name = "Документ пацієнта"
        verbose_name_plural = "Документи пацієнтів"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient.full_name} — {self.title}"


class Appointment(models.Model):
    """
    Запис на прийом.
    """

    class Status(models.TextChoices):
        NEW = "new", "Нова заявка"
        CONFIRMED = "confirmed", "Підтверджено"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Скасовано"
        NO_SHOW = "no_show", "Пацієнт не зʼявився"

    class Source(models.TextChoices):
        WEBSITE = "website", "Сайт"
        PHONE = "phone", "Дзвінок"
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        VIBER = "viber", "Viber"
        TELEGRAM = "telegram", "Telegram"
        OTHER = "other", "Інше"

    branch = models.ForeignKey(
        Branch,
        verbose_name="Філіал",
        on_delete=models.PROTECT,
        related_name="appointments"
    )
    service = models.ForeignKey(
        Service,
        verbose_name="Послуга",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments"
    )

    patient = models.ForeignKey(
        Patient,
        verbose_name="Пацієнт",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor,
        verbose_name="Лікар",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments"
    )

    # Данні пацієнта, які зберігаємо прямо в записі (щоб була історія, навіть якщо профіль зміниться)
    full_name = models.CharField("ПІБ пацієнта (на момент запису)", max_length=255)
    phone = models.CharField("Телефон", max_length=30)
    is_first_visit = models.BooleanField(
        "Перший візит",
        default=True
    )

    # Дата та час окремо, як ми планували
    date = models.DateField("Дата візиту")
    time = models.TimeField("Час візиту")

    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )

    note = models.TextField(
        "Коментар / опис проблеми",
        blank=True
    )
    internal_comment = models.TextField(
        "Внутрішній коментар для адміністраторів",
        blank=True
    )

    source = models.CharField(
        "Джерело заявки",
        max_length=20,
        choices=Source.choices,
        default=Source.WEBSITE
    )

    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Запис"
        verbose_name_plural = "Записи"
        ordering = ["-date", "-time", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "doctor", "date", "time"],
                condition=Q(status__in=["new", "confirmed"]),
                name="unique_slot_per_doctor_branch_for_active_statuses",
            )
        ]

    def __str__(self):
        doctor_name = self.doctor.full_name if self.doctor else "Без лікаря"
        return f"{self.full_name} — {self.date} {self.time} ({doctor_name})"

    @property
    def datetime_start(self):
        """
        datetime початку візиту.
        """
        return timezone.make_aware(
            timezone.datetime.combine(self.date, self.time),
            timezone.get_current_timezone()
        )

    @property
    def datetime_end(self):
        """
        Кінець візиту, враховуючи тривалість послуги.
        """
        if not self.service or not self.service.duration_min:
            return None
        return self.datetime_start + timezone.timedelta(minutes=self.service.duration_min)

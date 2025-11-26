from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


from django.utils.text import slugify


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
        max_digits=18,
        decimal_places=15,
        null=True,
        blank=True,
        help_text="Наприклад: 48.46371481421031"
    )
    longitude = models.DecimalField(
        "Довгота (lng)",
        max_digits=18,
        decimal_places=15,
        null=True,
        blank=True,
        help_text="Наприклад: 35.05316031300193"
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





class TreatmentCategory(models.Model):
    """
    Категорія / напрямок лікування з картинкою та прив'язкою до послуг.
    """
    title = models.CharField("Назва категорії", max_length=255)
    slug = models.SlugField("URL-ключ", max_length=255, unique=True, blank=True)

    image = models.ImageField(
        "Зображення",
        upload_to="treatments/",
        blank=True,
        null=True,
        help_text="Фото напряму лікування. Якщо не у WEBP, буде автоматично конвертовано."
    )

    short_description = models.TextField(
        "Короткий опис",
        max_length=400,
        help_text="Використовується на картці (2–3 речення)."
    )
    full_description = models.TextField(
        "Повний опис",
        help_text="Основний текст статті для окремої сторінки."
    )

    # 4 окремі пункти (переваги / показання / особливості)
    point_1 = models.CharField("Пункт 1", max_length=255, blank=True)
    point_2 = models.CharField("Пункт 2", max_length=255, blank=True)
    point_3 = models.CharField("Пункт 3", max_length=255, blank=True)
    point_4 = models.CharField("Пункт 4", max_length=255, blank=True)

    # зв'язок з послугами
    services = models.ManyToManyField(
        "Service",
        blank=True,
        related_name="treatment_categories",
        verbose_name="Пов'язані послуги"
    )

    sort_order = models.PositiveIntegerField("Порядок сортування", default=0)
    is_active = models.BooleanField("Показувати на сайті", default=True)
    created_at = models.DateTimeField("Створено", default=timezone.now)

    class Meta:
        verbose_name = "Категорія лікування"
        verbose_name_plural = "Категорії лікування"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # автогенерація slug
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while TreatmentCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug

        super().save(*args, **kwargs)

        # автоконвертація картинки в WEBP
        if self.image and not self.image.name.lower().endswith(".webp"):
            try:
                img = Image.open(self.image)
                img = img.convert("RGB")

                buffer = BytesIO()
                img.save(buffer, format="WEBP", quality=85)
                buffer.seek(0)

                original_name = self.image.name.rsplit(".", 1)[0]
                webp_name = f"{original_name}.webp"

                self.image.save(webp_name, ContentFile(buffer.read()), save=False)
                super().save(update_fields=["image"])
            except Exception:
                # якщо щось пішло не так з конвертацією – просто залишаємо як є
                pass


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

    # 🔹 новое — для карточки
    photo = models.ImageField(
        "Фото лікаря",
        upload_to="doctors/",
        null=True,
        blank=True,
        help_text="Фото лікаря (буде автоматично конвертовано у WEBP)"
    )
    date_of_birth = models.DateField("Дата народження", null=True, blank=True)
    short_title = models.CharField(
        "Посада / роль",
        max_length=255,
        blank=True,
        help_text="Наприклад: Лікар-стоматолог, ортодонт"
    )
    experience_years = models.PositiveIntegerField(
        "Стаж (років)",
        null=True,
        blank=True
    )
    skills = models.CharField(
        "Ключові навички",
        max_length=255,
        blank=True,
        help_text="Через кому: імплантація, ортопедія, терапія"
    )
    bio = models.TextField(
        "Короткий опис",
        blank=True,
        help_text="Кілька речень про лікаря для зворотньої сторони картки"
    )

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
    
    
    def save(self, *args, **kwargs):
        """
        При сохранении:
        - якщо фото не webp → конвертуємо у WEBP
        - старий оригінальний файл (jpg/png/…) видаляємо з диску
        - не дублюємо шлях 'doctors/doctors/...'
        """
        # Сохраняем объект первый раз, чтобы файл появился в файловой системе
        super().save(*args, **kwargs)

        if not self.photo:
            return

        # Уже webp — выходим
        if self.photo.name.lower().endswith(".webp"):
            return

        # Путь к исходному файлу, чтобы потом удалить
        try:
            original_path = self.photo.path
        except Exception:
            original_path = None

        # Открываем картинку
        try:
            img = Image.open(self.photo)
        except Exception:
            return

        img = img.convert("RGB")

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=85)
        buffer.seek(0)

        # ⚠️ Берём только имя файла без папок
        # было: base, ext = os.path.splitext(self.photo.name)
        # стало:
        dir_name, file_name = os.path.split(self.photo.name)
        base, ext = os.path.splitext(file_name)
        new_name = base + ".webp"  # upload_to добавится автоматически

        # Сохраняем webp в ту же папку `doctors/`
        self.photo.save(new_name, ContentFile(buffer.read()), save=False)

        # Финальное сохранение
        super().save(update_fields=["photo"])

        # Удаляем исходный файл
        if original_path and os.path.exists(original_path) and original_path != self.photo.path:
            try:
                os.remove(original_path)
            except OSError:
                pass

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years



class DoctorSchedule(models.Model):
    """
    Базовий (тижневий) графік роботи лікаря.
    Використовується як шаблон, якщо на конкретну дату
    немає індивідуального розкладу.
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
        related_name="weekly_schedules",
    )
    branch = models.ForeignKey(
        Branch,
        verbose_name="Філіал",
        on_delete=models.CASCADE,
        related_name="doctor_weekly_schedules",
    )
    weekday = models.IntegerField("День тижня", choices=WeekDay.choices)
    start_time = models.TimeField("Початок прийому")
    end_time = models.TimeField("Кінець прийому")
    break_start = models.TimeField("Початок обіду", null=True, blank=True)
    break_end = models.TimeField("Кінець обіду", null=True, blank=True)
    is_active = models.BooleanField("Працює в цей день", default=True)

    class Meta:
        verbose_name = "Тижневий графік лікаря"
        verbose_name_plural = "Тижневі графіки лікарів"
        unique_together = ("doctor", "weekday", "branch")
        ordering = ["doctor", "weekday"]

    def __str__(self):
        return f"{self.doctor.full_name} — {self.get_weekday_display()} ({self.branch.name})"

class DoctorDaySchedule(models.Model):
    """
    Індивідуальний графік лікаря на КОНКРЕТНУ дату.

    Якщо існує запис для (doctor, branch, date),
    він ПЕРЕЗАТЕРІЄ тижневий шаблон DoctorSchedule.
    """
    doctor = models.ForeignKey(
        Doctor,
        verbose_name="Лікар",
        on_delete=models.CASCADE,
        related_name="day_schedules",
    )
    branch = models.ForeignKey(
        Branch,
        verbose_name="Філіал",
        on_delete=models.CASCADE,
        related_name="doctor_day_schedules",
    )
    date = models.DateField("Дата")
    start_time = models.TimeField("Початок прийому", null=True, blank=True)
    end_time = models.TimeField("Кінець прийому", null=True, blank=True)
    break_start = models.TimeField("Початок обіду", null=True, blank=True)
    break_end = models.TimeField("Кінець обіду", null=True, blank=True)
    is_working = models.BooleanField(
        "Працює у цей день",
        default=True,
        help_text="Якщо зняти галочку — лікар у відпустці / лікар не приймає."
    )
    note = models.CharField("Примітка", max_length=255, blank=True)

    class Meta:
        verbose_name = "Денний графік лікаря"
        verbose_name_plural = "Денні графіки лікарів"
        unique_together = ("doctor", "branch", "date")
        ordering = ["date", "doctor"]

    def __str__(self):
        return f"{self.date} — {self.doctor.full_name} ({self.branch.name})"


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

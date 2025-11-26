from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404

from .models import Branch, Service, Appointment, Patient, Doctor, DoctorSchedule, DoctorDaySchedule,TreatmentCategory
from django.http import JsonResponse
from django.contrib.auth import get_user_model, login
from django.urls import reverse
from datetime import datetime, timedelta, time
from django.utils import timezone

from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404


def index(request):
    """
    Лендинг стоматології.
    """
    branches = Branch.objects.filter(is_active=True).order_by("sort_order")

    # 🔹 все активные услуги
    services_qs = Service.objects.filter(is_active=True).order_by("name")

    # 🔹 пагинация по 5 услуг
    paginator = Paginator(services_qs, 5)
    page_number = request.GET.get("services_page") or 1
    services_page = paginator.get_page(page_number)


    treatments_qs = (
        TreatmentCategory.objects
        .filter(is_active=True)
        .exclude(slug__isnull=True)
        .exclude(slug__exact="")
        .order_by("title")
    )
    treatments_paginator = Paginator(treatments_qs, 10)  # до 10 карток на сторінці
    treatments_page_number = request.GET.get("treatments_page") or 1
    treatments_page = treatments_paginator.get_page(treatments_page_number)

    # 🔹 врачи для баннера
    hero_doctors = (
        Doctor.objects.filter(is_active=True)
        .select_related("branch")
        .order_by("full_name")[:4]
    )

    return render(request, "booking/index.html", {
        "branches": branches,
        "services": services_page,   # 👈 теперь это Page-объект
        "hero_doctors": hero_doctors,
        "treatments": treatments_page, 
        "page_id": "landing",
    })



@login_required
def patient_dashboard(request):
    """
    Кабінет пацієнта після логіну + статистика.
    """
    patient = getattr(request.user, "patient_profile", None)
    if not patient:
        raise Http404("Профіль пацієнта не знайдено")

    appointments_qs = (
        patient.appointments
        .select_related("doctor", "branch", "service")
        .order_by("-date", "-time")
    )

    # --------- Статистика по записах ----------
    total_appointments = appointments_qs.count()
    today = timezone.localdate()

    upcoming_appointments = appointments_qs.filter(
        date__gte=today,
        status__in=[Appointment.Status.NEW, Appointment.Status.CONFIRMED],
    ).count()

    completed_appointments = appointments_qs.filter(
        status=Appointment.Status.COMPLETED
    ).count()

    cancelled_appointments = appointments_qs.filter(
        status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW]
    ).count()

    # Орієнтовно, скільки пацієнт витратив:
    # беремо price_from з послуг у завершених візитах
    completed_qs = appointments_qs.filter(
        status=Appointment.Status.COMPLETED,
        service__price_from__isnull=False,
    )

    total_spent = (
        completed_qs.aggregate(total=Sum("service__price_from"))["total"] or 0
    )

    # Статистика по послугах для "діаграми"
    per_service_raw = list(
        completed_qs.values("service__name")
        .annotate(
            count=Count("id"),
            amount=Sum("service__price_from"),
        )
        .order_by("-amount")
    )

    total_amount = sum((row["amount"] or 0) for row in per_service_raw) or 0

    service_stats = []
    for row in per_service_raw:
        amount = row["amount"] or 0
        percent = int(amount / total_amount * 100) if total_amount else 0
        service_stats.append(
            {
                "name": row["service__name"] or "Послуга",
                "count": row["count"],
                "amount": amount,
                "percent": percent,
            }
        )

    # Документи пацієнта
    patient_docs = patient.documents.all().order_by("-created_at")

    return render(
        request,
        "booking/patient_dashboard.html",
        {
            "patient": patient,
            "appointments": appointments_qs,
            "patient_docs": patient_docs,
            "page_id": "patient_dashboard",
            "stats": {
                "total": total_appointments,
                "upcoming": upcoming_appointments,
                "completed": completed_appointments,
                "cancelled": cancelled_appointments,
                "total_spent": total_spent,
            },
            "service_stats": service_stats,
        },
    )

@login_required
def doctor_patient_detail(request, patient_id):
    """
    Детальна картка пацієнта для лікаря / адміністратора:
    - інфа про пацієнта
    - візити (з фільтрами + пагінацією)
    - статистика
    - документи
    """
    doctor = getattr(request.user, "doctor_profile", None)
    if not doctor and not request.user.is_staff and not request.user.is_superuser:
        raise Http404("Доступ заборонено")

    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        raise Http404("Пацієнта не знайдено")

    base_qs = (
        Appointment.objects
        .filter(patient=patient)
        .select_related("doctor", "branch", "service", "patient")
        .order_by("-date", "-time")
    )

    # якщо лікар (а не адмін) — показуємо тільки його візити
    if doctor and not request.user.is_superuser:
        base_qs = base_qs.filter(doctor=doctor)

    # --------- ФІЛЬТРИ ---------
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""
    service_id = request.GET.get("service") or ""

    filters_q = Q()
    if start_date:
        filters_q &= Q(date__gte=start_date)
    if end_date:
        filters_q &= Q(date__lte=end_date)
    if service_id:
        filters_q &= Q(service_id=service_id)

    filtered_qs = base_qs.filter(filters_q)

    # --------- ПАГІНАЦІЯ ---------
    paginator = Paginator(filtered_qs, 6)  # по 6 візитів на сторінку
    page_number = request.GET.get("page") or 1
    appointments_page = paginator.get_page(page_number)

    # --------- СТАТИСТИКА ---------
    total_visits = filtered_qs.count()
    completed_visits = filtered_qs.filter(status=Appointment.Status.COMPLETED).count()
    cancelled_visits = filtered_qs.filter(
        status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW]
    ).count()

    first_visit = filtered_qs.last()
    last_visit = filtered_qs.first()

    completed_paid = filtered_qs.filter(
        status=Appointment.Status.COMPLETED,
        service__price_from__isnull=False,
    )
    total_amount = completed_paid.aggregate(
        total=Sum("service__price_from")
    )["total"] or 0

    per_service_raw = list(
        completed_paid.values("service__name")
        .annotate(
            count=Count("id"),
            amount=Sum("service__price_from"),
        )
        .order_by("-amount")
    )
    service_stats = [
        {
            "name": row["service__name"] or "Послуга",
            "count": row["count"],
            "amount": row["amount"] or 0,
        }
        for row in per_service_raw
    ]

    documents = patient.documents.all().order_by("-created_at")

    # для збереження фільтрів в пагінації
    qs_params = {}
    if start_date:
        qs_params["start_date"] = start_date
    if end_date:
        qs_params["end_date"] = end_date
    if service_id:
        qs_params["service"] = service_id
    qs_base = "&" + urlencode(qs_params) if qs_params else ""

    context = {
        "patient": patient,
        "appointments_page": appointments_page,
        "documents": documents,
        "stats": {
            "total_visits": total_visits,
            "completed_visits": completed_visits,
            "cancelled_visits": cancelled_visits,
            "first_visit": first_visit,
            "last_visit": last_visit,
            "total_amount": total_amount,
            "service_stats": service_stats,
        },
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "service_id": service_id,
            "qs_base": qs_base,
        },
        "services_all": Service.objects.filter(is_active=True).order_by("name"),
        "page_id": "doctor_patient_detail",
    }

    return render(request, "booking/doctor_patient_detail.html", context)


from django.views.decorators.http import require_POST

@login_required
@require_POST
def api_update_appointment(request, appointment_id):
    """
    Оновлення нотатки та послуги для конкретного візиту (картки) через AJAX.
    """
    doctor = getattr(request.user, "doctor_profile", None)
    user = request.user

    try:
        appt = Appointment.objects.select_related("doctor", "patient").get(id=appointment_id)
    except Appointment.DoesNotExist:
        return JsonResponse({"success": False, "error": "Запис не знайдено."}, status=404)

    # Права доступу: свій пацієнт для лікаря або адмін
    if doctor and not user.is_superuser:
        if appt.doctor_id != doctor.id:
            return JsonResponse({"success": False, "error": "Немає доступу."}, status=403)
    elif not doctor and not user.is_staff and not user.is_superuser:
        return JsonResponse({"success": False, "error": "Немає доступу."}, status=403)

    note = request.POST.get("note", "").strip()
    service_id = request.POST.get("service_id") or ""

    # оновлюємо нотатку
    appt.note = note

    # оновлюємо послугу
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
            appt.service = service
        except Service.DoesNotExist:
            pass
    else:
        appt.service = None

    appt.save()

    return JsonResponse({
        "success": True,
        "note": appt.note,
        "service": appt.service.name if appt.service else "",
    })


@login_required
def doctor_dashboard(request):
    """
    Кабінет лікаря / адміна:
    - лікар бачить свої записи
    - суперюзер може бачити всі та фільтрувати по лікарю
    """
    doctor = getattr(request.user, "doctor_profile", None)

    if not doctor and not request.user.is_superuser:
        raise Http404("Профіль лікаря не знайдено")

    # Базова вибірка (для статистики "всього")
    base_qs = (
        Appointment.objects
        .select_related("patient", "doctor", "branch", "service")
        .order_by("-date", "-time")
    )

    # Якщо це не суперюзер — показуємо тільки візити цього лікаря
    if doctor and not request.user.is_superuser:
        base_qs = base_qs.filter(doctor=doctor)

    # ---- Фільтри з GET ----
    date_from_str = request.GET.get("date_from", "").strip()
    date_to_str = request.GET.get("date_to", "").strip()
    status = request.GET.get("status", "").strip()
    branch_id = request.GET.get("branch", "").strip()
    doctor_id = request.GET.get("doctor", "").strip()
    patient_query = request.GET.get("patient", "").strip()

    filtered_qs = base_qs

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            filtered_qs = filtered_qs.filter(date__gte=date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            filtered_qs = filtered_qs.filter(date__lte=date_to)
        except ValueError:
            pass

    if status:
        filtered_qs = filtered_qs.filter(status=status)

    if branch_id:
        filtered_qs = filtered_qs.filter(branch_id=branch_id)

    # Для суперюзера даємо можливість вибрати лікаря з селекту
    if request.user.is_superuser and doctor_id:
        filtered_qs = filtered_qs.filter(doctor_id=doctor_id)

    if patient_query:
        filtered_qs = filtered_qs.filter(
            Q(patient__full_name__icontains=patient_query)
            | Q(full_name__icontains=patient_query)
            | Q(patient__phone__icontains=patient_query)
            | Q(phone__icontains=patient_query)
        )

    appointments = filtered_qs

    # ---- Статистика "всього" (по base_qs без фільтрів) ----
    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    total_appointments = base_qs.count()
    today_appointments = base_qs.filter(date=today).count()
    week_appointments = base_qs.filter(date__gte=start_of_week, date__lte=end_of_week).count()

    completed_total = base_qs.filter(status=Appointment.Status.COMPLETED).count()
    cancelled_total = base_qs.filter(
        status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW]
    ).count()

    unique_patients = (
        base_qs.exclude(patient__isnull=True)
        .values("patient_id")
        .distinct()
        .count()
    )

    spent_total = (
        base_qs.filter(
            status=Appointment.Status.COMPLETED,
            service__price_from__isnull=False,
        ).aggregate(total=Sum("service__price_from"))["total"]
        or 0
    )

    stats_overall = {
        "total": total_appointments,
        "today": today_appointments,
        "week": week_appointments,
        "completed": completed_total,
        "cancelled": cancelled_total,
        "patients": unique_patients,
        "spent_total": spent_total,
    }

    # ---- Статистика по послугах (по вибірці з фільтрами) ----
    completed_filtered = filtered_qs.filter(
        status=Appointment.Status.COMPLETED,
        service__price_from__isnull=False,
    )

    per_service_raw = list(
        completed_filtered.values("service__name")
        .annotate(
            count=Count("id"),
            amount=Sum("service__price_from"),
        )
        .order_by("-amount")
    )

    total_amount = sum((row["amount"] or 0) for row in per_service_raw) or 0

    service_stats = []
    for row in per_service_raw:
        amount = row["amount"] or 0
        percent = int(amount / total_amount * 100) if total_amount else 0
        service_stats.append(
            {
                "name": row["service__name"] or "Послуга",
                "count": row["count"],
                "amount": amount,
                "percent": percent,
            }
        )

    # Для селектів у фільтрах
    branches = Branch.objects.filter(is_active=True).order_by("sort_order", "name")
    doctors_all = Doctor.objects.all().order_by("full_name")

    return render(
        request,
        "booking/doctor_dashboard.html",
        {
            "doctor": doctor,
            "appointments": appointments,
            "branches": branches,
            "doctors_all": doctors_all,
            "stats_overall": stats_overall,
            "service_stats": service_stats,
            "filters": {
                "date_from": date_from_str,
                "date_to": date_to_str,
                "status": status,
                "branch": branch_id,
                "doctor": doctor_id,
                "patient": patient_query,
            },
            "page_id": "doctor_dashboard",
        },
    )

User = get_user_model()


def register(request):
    """
    Реєстрація пацієнта без Django forms: в'ю + JS.
    GET -> повертає сторінку з формою
    POST -> приймає дані, валідуює, створює User + Patient, логінить і повертає JSON
    """
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("patient_dashboard")

        branches = Branch.objects.filter(is_active=True).order_by("sort_order")
        return render(request, "booking/register.html", {
            "page_id": "register",
            "branches": branches,
        })

    # POST
    data = request.POST

    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    date_of_birth_raw = data.get("date_of_birth", "").strip()
    branch_id = data.get("branch", "").strip()
    password1 = data.get("password1", "")
    password2 = data.get("password2", "")

    errors = {}

    # Валідація
    if not full_name:
        errors["full_name"] = "Вкажіть, будь ласка, ПІБ."
    if not phone:
        errors["phone"] = "Вкажіть номер телефону."
    if not password1:
        errors["password1"] = "Придумайте пароль."
    if password1 and len(password1) < 6:
        errors["password1"] = "Пароль має бути не коротше 6 символів."
    if password1 != password2:
        errors["password2"] = "Паролі не співпадають."

    # Унікальність email (не обов'язковий, але якщо є — перевіряємо)
    if email and User.objects.filter(email=email).exists():
        errors["email"] = "Користувач з таким email вже існує."

    # Дата народження (опціонально)
    date_of_birth = None
    if date_of_birth_raw:
        try:
            date_of_birth = datetime.strptime(date_of_birth_raw, "%Y-%m-%d").date()
        except ValueError:
            errors["date_of_birth"] = "Некоректний формат дати."

    # Філіал (опціонально, але краще обрати)
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            errors["branch"] = "Обраний філіал не знайдено."

    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    # Створюємо користувача
    username = email or phone
    if not username:
        username = f"user_{int(timezone.now().timestamp())}"

    user = User.objects.create_user(
        username=username,
        email=email or "",
        password=password1,
        is_active=True,
    )

    # Створюємо пацієнта
    patient = Patient.objects.create(
        user=user,
        full_name=full_name,
        phone=phone,
        email=email or "",
        date_of_birth=date_of_birth,
        branch=branch,
    )

    # Автовхід
    login(request, user)

    return JsonResponse({
        "success": True,
        "redirect_url": reverse("patient_dashboard"),
    })




from django.views.decorators.http import require_GET, require_POST
from django.db.models import Prefetch

# ...

@require_GET
def api_day_schedule(request):
    """
    Повертає список лікарів та зайняті/вільні слоти на конкретну дату
    з урахуванням:
    - тижневого графіку DoctorSchedule
    - денного оверрайду DoctorDaySchedule
    - вибраної філії (branch)
    """
    date_str = request.GET.get("date")
    branch_id = request.GET.get("branch")

    if not date_str:
        return JsonResponse({"error": "Потрібен параметр date (YYYY-MM-DD)."}, status=400)

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Некоректний формат дати."}, status=400)

    weekday_index = day.weekday()  # Monday=0

    # Базовый набор докторов
    doctors_qs = Doctor.objects.filter(is_active=True).select_related("branch")
    if branch_id:
        doctors_qs = doctors_qs.filter(branch_id=branch_id)

    # ---- Тижневий графік (шаблон) ----
    weekly_qs = DoctorSchedule.objects.filter(
        weekday=weekday_index,
        is_active=True,
        doctor__in=doctors_qs,
    )
    if branch_id:
        weekly_qs = weekly_qs.filter(branch_id=branch_id)

    weekly_by_doctor = {s.doctor_id: s for s in weekly_qs}

    # ---- Денний override ----
    day_qs = DoctorDaySchedule.objects.filter(
        date=day,
        doctor__in=doctors_qs,
    )
    if branch_id:
        day_qs = day_qs.filter(branch_id=branch_id)

    day_by_doctor = {s.doctor_id: s for s in day_qs}

    # ---- Вираховуємо ефективний графік на цей день ----
    effective_schedule = {}  # doctor_id -> object з полями start_time, end_time, branch
    for doctor in doctors_qs:
        day_sched = day_by_doctor.get(doctor.id)
        if day_sched:
            # денний override
            if not day_sched.is_working:
                continue  # сьогодні не працює
            if not day_sched.start_time or not day_sched.end_time:
                continue  # некоректний запис
            effective_schedule[doctor.id] = day_sched
        else:
            # тижневий графік
            week_sched = weekly_by_doctor.get(doctor.id)
            if not week_sched:
                continue
            if not week_sched.is_active:
                continue
            effective_schedule[doctor.id] = week_sched

    # Якщо в цей день ніхто не працює
    if not effective_schedule:
        return JsonResponse({
            "date": day.isoformat(),
            "hours": [],
            "doctors": [],
        })

    # Обмежуємо список лікарів тільки тими, хто реально працює в цей день
    working_doctor_ids = list(effective_schedule.keys())
    doctors_qs = doctors_qs.filter(id__in=working_doctor_ids)

    # ---- Формуємо діапазон годин для сітки ----
    all_starts = []
    all_ends = []
    for sched in effective_schedule.values():
        all_starts.append(sched.start_time.hour)
        all_ends.append(sched.end_time.hour)

    start_hour = min(all_starts)
    end_hour = max(all_ends)

    # наприклад, 9..18 → ["09:00", ..., "17:00"]
    slot_minutes = 30  # базовый шаг слота
    start_dt = datetime.combine(day, time(hour=start_hour, minute=0))
    end_dt = datetime.combine(day, time(hour=end_hour, minute=0))

    hours = []
    cur = start_dt
    while cur < end_dt:
        hours.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=slot_minutes)

    # ---- Тягнемо апойтменти для цих лікарів на цю дату ----
    appointments = Appointment.objects.filter(
        date=day,
        doctor__in=doctors_qs,
        status__in=[Appointment.Status.NEW, Appointment.Status.CONFIRMED],
    ).select_related("doctor", "service", "patient")

    busy_map = {}  # doctor_id -> { "HH:MM": {...} }
    for appt in appointments:
        key = appt.time.strftime("%H:%M")
        busy_map.setdefault(appt.doctor_id, {})
        busy_map[appt.doctor_id][key] = {
            "id": appt.id,
            "status": appt.status,
            "service": appt.service.name if appt.service else "",
            "patient": getattr(appt.patient, "full_name", appt.full_name),
        }

    doctors_data = []
    for doctor in doctors_qs:
        sched = effective_schedule.get(doctor.id)
        if not sched:
            continue

        work_start = sched.start_time.strftime("%H:%M")
        work_end = sched.end_time.strftime("%H:%M")
        doc_busy = busy_map.get(doctor.id, {})

        doctors_data.append({
            "id": doctor.id,
            "name": doctor.full_name,
            "branch": doctor.branch.name if getattr(doctor, "branch", None) else "",
            "branch_id": doctor.branch_id,
            "work_start": work_start,
            "work_end": work_end,
            "break_start": sched.break_start.strftime("%H:%M") if getattr(sched, "break_start", None) else None,
            "break_end": sched.break_end.strftime("%H:%M") if getattr(sched, "break_end", None) else None,
            "busy_slots": doc_busy,
        })

    return JsonResponse({
        "date": day.isoformat(),
        "hours": hours,
        "doctors": doctors_data,
    })


@login_required
@require_POST
def api_create_appointment(request):
    """
    Створення запису на прийом з віджета календаря.
    Працює тільки для залогінених пацієнтів.
    """
    patient = getattr(request.user, "patient_profile", None)
    if not patient:
        return JsonResponse({"error": "Профіль пацієнта не знайдено."}, status=400)

    data = request.POST
    date_str = data.get("date")
    time_str = data.get("time")
    branch_id = data.get("branch_id")
    doctor_id = data.get("doctor_id")
    service_id = data.get("service_id")
    note = data.get("note", "").strip()

    errors = {}

    if not date_str:
        errors["date"] = "Оберіть дату."
    if not time_str:
        errors["time"] = "Оберіть час."
    if not doctor_id:
        errors["doctor"] = "Оберіть лікаря."

    # Валідацію філіалу поки відкладаємо — спробуємо взяти з лікаря, якщо не прийшов
    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "errors": {"date": "Некоректна дата."}}, status=400)

    try:
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return JsonResponse({"success": False, "errors": {"time": "Некоректний час."}}, status=400)

    # Спочатку дістаємо лікаря
    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return JsonResponse({"success": False, "errors": {"doctor": "Лікаря не знайдено."}}, status=400)

    # Тепер визначаємо філіал:
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({"success": False, "errors": {"branch": "Філіал не знайдено."}}, status=400)
    else:
        # Якщо філіал не передали — пробуємо взяти з лікаря
        if doctor.branch_id:
            branch = doctor.branch
        else:
            return JsonResponse(
                {"success": False, "errors": {"branch": "Для цього лікаря не вказаний філіал."}},
                status=400
            )

    service = None
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            service = None

    # Захист від дублю слоту по лікарю
    if Appointment.objects.filter(
        doctor=doctor,
        date=day,
        time=t,
        status__in=["new", "confirmed"]
    ).exists():
        return JsonResponse({
            "success": False,
            "errors": {"slot": "Цей час вже зайнятий."}
        }, status=400)

    appt = Appointment.objects.create(
        branch=branch,
        service=service,
        full_name=patient.full_name,
        phone=patient.phone,
        is_first_visit=True,
        date=day,
        time=t,
        status=Appointment.Status.NEW,
        note=note,
        source=Appointment.Source.WEBSITE,
        patient=patient,
        doctor=doctor,
    )

    return JsonResponse({
        "success": True,
        "appointment_id": appt.id,
    })



@login_required
def profile_redirect(request):
    """
    Куди відправляти користувача після логіну.
    """
    user = request.user

    # якщо є профіль лікаря
    if hasattr(user, "doctor_profile"):
        return redirect("doctor_dashboard")

    # якщо є профіль пацієнта
    if hasattr(user, "patient_profile"):
        return redirect("patient_dashboard")

    # якщо адмін/персонал без профілю
    if user.is_staff or user.is_superuser:
        return redirect("/admin/")

    # запасний варіант — на головну
    return redirect("index")



def logout_view(request):
    """
    Универсальный выход для любого пользователя.
    Работает по GET и по POST.
    """
    logout(request)
    return redirect("index")  # или куда надо: "patient_dashboard" / "doctor_dashboard"




def treatment_category_detail(request, slug):
    """
    Детальна сторінка категорії лікування:
    - фото (якщо є)
    - повний текст
    - 4 ключові пункти
    - прив'язані послуги
    - лінки на інші категорії
    """
    category = get_object_or_404(
        TreatmentCategory,
        slug=slug,
        is_active=True,
    )

    # послуги, прив'язані до цієї категорії (через M2M)
    related_services = category.services.filter(is_active=True).order_by("name") if hasattr(category, "services") else []

    # інші категорії для блоку "Інші напрямки лікування"
    other_categories = (
        TreatmentCategory.objects.filter(is_active=True)
        .exclude(id=category.id)
        .order_by("title")[:6]
    )

    return render(
        request,
        "booking/treatment_category_detail.html",
        {
            "category": category,
            "related_services": related_services,
            "other_categories": other_categories,
        },
    )
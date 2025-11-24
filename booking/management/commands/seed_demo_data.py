import random
from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from booking.models import (
    Branch,
    BranchWorkHour,
    Service,
    Patient,
    Doctor,
    DoctorSchedule,
    PatientDocument,
    Appointment,
)


class Command(BaseCommand):
    help = "Створює демо-дані для стоматології (філіали, лікарі, пацієнти, записи на тиждень вперед)."

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.MIGRATE_HEADING("Створення демо-даних..."))

        # --- ФІЛІАЛИ ---
        addresses = [
            "вул. Центральна, 12",
            "просп. Свободи, 45",
            "вул. Пушкіна, 7",
            "вул. Грушевського, 23",
        ]

        branches = []
        for i, addr in enumerate(addresses, start=1):
            branch, created = Branch.objects.get_or_create(
                code=f"dnp-{i}",
                defaults={
                    "name": f"Стоматологія #{i}",
                    "city": "Дніпро",
                    "address": addr,
                    "phone_main": "+38067123456" + str(i),
                    "email": f"clinic{i}@example.com",
                    "is_active": True,
                    "sort_order": i,
                }
            )
            branches.append(branch)

        self.stdout.write(self.style.SUCCESS(f"Філіалів: {len(branches)}"))

        # --- ГОДИНИ РОБОТИ ФІЛІАЛІВ ---
        for branch in branches:
            for weekday in range(7):
                defaults = {}
                if weekday == 6:  # неділя
                    defaults.update({"is_closed": True})
                else:
                    defaults.update({
                        "is_closed": False,
                        "opens_at": time(9, 0),
                        "closes_at": time(18, 0),
                    })
                BranchWorkHour.objects.update_or_create(
                    branch=branch,
                    weekday=weekday,
                    defaults=defaults,
                )

        self.stdout.write(self.style.SUCCESS("Години роботи філіалів оновлено."))

        # --- ПОСЛУГИ ---
        services_data = [
            ("Консультація стоматолога", "Первинний огляд, план лікування.", 30, 400),
            ("Лікування карієсу", "Пломбування зубів сучасними матеріалами.", 60, 1200),
            ("Професійна гігієна", "Ультразвукова чистка, полірування.", 60, 1500),
            ("Видалення зуба", "Атравматичне видалення зубів.", 45, 1800),
        ]

        services = []
        for name, desc, duration, price in services_data:
            srv, _ = Service.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "duration_min": duration,
                    "price_from": price,
                    "is_active": True,
                }
            )
            services.append(srv)

        self.stdout.write(self.style.SUCCESS(f"Послуг: {len(services)}"))

        # --- ЛІКАРІ (User + Doctor) ---
        doctors = []
        doctor_specs = [
            ("doc1", "doctor1@example.com", "Доктор Іваненко Іван Іванович", "Терапевт"),
            ("doc2", "doctor2@example.com", "Доктор Петрова Олена Сергіївна", "Ортопед"),
        ]

        for i, (username, email, full_name, spec) in enumerate(doctor_specs):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": True,
                    "is_active": True,
                }
            )
            if created:
                user.set_password("doctor1234")
                user.save()

            branch = branches[i % len(branches)]

            doctor, _ = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "specialization": spec,
                    "branch": branch,
                    "phone": "+380501112233",
                    "is_active": True,
                }
            )
            doctors.append(doctor)

        self.stdout.write(self.style.SUCCESS(f"Лікарів: {len(doctors)} (логін: doc1/doc2, пароль: doctor1234)"))

        # --- ГРАФІК ЛІКАРІВ ---
        for doctor in doctors:
            for weekday in range(0, 6):  # Пн-Сб
                DoctorSchedule.objects.update_or_create(
                    doctor=doctor,
                    branch=doctor.branch,
                    weekday=weekday,
                    defaults={
                        "start_time": time(10, 0),
                        "end_time": time(16, 0),
                        "is_active": True,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Графік лікарів оновлено."))

        # --- ПАЦІЄНТИ (User + Patient) ---
        patients = []

        patients_data = [
            ("patient1", "patient1@example.com", "Пацієнт Коваленко Максим", "+380501234567"),
            ("patient2", "patient2@example.com", "Пацієнтка Шевченко Анна", "+380671234568"),
        ]

        for i, (username, email, full_name, phone) in enumerate(patients_data):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_active": True,
                }
            )
            if created:
                user.set_password("patient1234")
                user.save()

            branch = branches[i % len(branches)]

            patient, _ = Patient.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "phone": phone,
                    "email": email,
                    "branch": branch,
                }
            )
            patients.append(patient)

        self.stdout.write(self.style.SUCCESS(f"Пацієнтів: {len(patients)} (логін: patient1/patient2, пароль: patient1234)"))

        # --- ДОКУМЕНТИ ПАЦІЄНТІВ (фейкові записи без реального файлу) ---
        # Якщо файли не потрібні — можна пропустити або використовувати маленькі pdf з медіа
        for patient in patients:
            PatientDocument.objects.get_or_create(
                patient=patient,
                title="Результати огляду",
                defaults={
                    "description": "Тестовий документ (файл не завантажений).",
                    # file обов'язковий в моделі, тому тут краще мати хоча б якийсь файл у медіа,
                    # але для демо можна потім підвантажити руками.
                }
            )

        self.stdout.write(self.style.WARNING("Документи пацієнтів створені (може знадобитися завантажити файли вручну)."))

        # --- ЗАПИСИ НА ПРИЙОМ (сьогодні + 7 днів) ---
        today = timezone.localdate()
        days_ahead = 7

        created_count = 0

        for day_offset in range(days_ahead + 1):
            date = today + timedelta(days=day_offset)

            for doctor in doctors:
                # 2–3 записи на день
                slots = [time(10, 0), time(11, 30), time(13, 0), time(14, 30), time(16, 0)]
                random.shuffle(slots)
                for slot in slots[:3]:
                    patient = random.choice(patients)
                    service = random.choice(services)
                    branch = doctor.branch

                    Appointment.objects.get_or_create(
                        branch=branch,
                        doctor=doctor,
                        date=date,
                        time=slot,
                        defaults={
                            "service": service,
                            "patient": patient,
                            "full_name": patient.full_name,
                            "phone": patient.phone,
                            "is_first_visit": random.choice([True, False]),
                            "status": random.choice([
                                Appointment.Status.NEW,
                                Appointment.Status.CONFIRMED
                            ]),
                            "note": "Тестовий запис, створений автоматично.",
                            "source": Appointment.Source.WEBSITE,
                        }
                    )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Створено/оновлено записів на прийом: {created_count}"))

        self.stdout.write(self.style.SUCCESS("Готово! Демодані успішно створено."))

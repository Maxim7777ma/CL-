from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),  # лендинг
    path("register/", views.register, name="register"),
    path("patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path(
        "doctor/patient/<int:patient_id>/",
        views.doctor_patient_detail,
        name="doctor_patient_detail",
    ),
    path(
        "doctor/api/appointment/<int:appointment_id>/update/",
        views.api_update_appointment,
        name="api_update_appointment",
    ),

    path("api/day-schedule/", views.api_day_schedule, name="api_day_schedule"),
    path("api/create-appointment/", views.api_create_appointment, name="api_create_appointment"),
]

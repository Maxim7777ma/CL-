from django.contrib import admin
from django.urls import path, include
from booking import views as booking_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/profile/", booking_views.profile_redirect, name="profile_redirect"),
    path('accounts/', include('django.contrib.auth.urls')),  # логін/логаут
    path('', include('booking.urls')),
]

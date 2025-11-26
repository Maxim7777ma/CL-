from django.contrib import admin
from django.urls import path, include
from booking import views as booking_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/profile/", booking_views.profile_redirect, name="profile_redirect"),
    path("accounts/logout/", booking_views.logout_view, name="logout"),
    path('accounts/', include('django.contrib.auth.urls')),  # логін/логаут
    path('', include('booking.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
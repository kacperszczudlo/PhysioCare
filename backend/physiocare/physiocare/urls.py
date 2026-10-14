from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.media_views import ProtectedMediaServeView
from documents.urls import me_urlpatterns as documents_me_urls
from exercises.urls import me_urlpatterns as exercises_me_urls
from notifications.urls import me_urlpatterns as notifications_me_urls
from patients.urls import me_urlpatterns as patients_me_urls
from scheduling.urls import me_urlpatterns as scheduling_me_urls
from treatment.urls import me_urlpatterns as treatment_me_urls

me_urlpatterns: list[URLPattern | URLResolver] = (
    patients_me_urls
    + scheduling_me_urls
    + exercises_me_urls
    + documents_me_urls
    + notifications_me_urls
    + treatment_me_urls
)

urlpatterns: list[URLPattern | URLResolver] = [
    path('admin/', admin.site.urls),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/patients/', include('patients.urls')),
    path('api/v1/me/', include((me_urlpatterns, 'me'))),
    path('api/v1/', include('treatment.urls')),
    path('api/v1/', include('scheduling.urls')),
    path('api/v1/', include('exercises.urls')),
    path('api/v1/', include('documents.urls')),
    path('api/v1/', include('therapists.urls')),
    path('api/v1/', include('reviews.urls')),
    path('api/v1/admin/', include('administration.urls')),
    path('media/<path:path>', ProtectedMediaServeView.as_view(), name='protected-media'),
]

from django.contrib import admin

from notifications.models import DeviceToken, NotificationDelivery, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Panel administracyjny dla preferencji powiadomień użytkowników."""

    list_display = ('user', 'pref_key', 'enabled')
    list_filter = ('pref_key', 'enabled')
    search_fields = ('user__email',)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    """Panel administracyjny dla tokenów urządzeń mobilnych."""

    list_display = ('user', 'platform', 'is_active', 'updated_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('user__email',)


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    """Panel administracyjny dla historii dostarczenia powiadomień."""

    list_display = ('user', 'pref_key', 'channel', 'status', 'created_at')
    list_filter = ('pref_key', 'channel', 'status')
    search_fields = ('user__email', 'title')
    readonly_fields = ('created_at',)

from django.contrib import admin

from .models import AccountDeletionRequest, Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted', 'granted_at')
    list_filter = ('consent_type', 'granted')
    search_fields = ('user__email',)


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'processed_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)

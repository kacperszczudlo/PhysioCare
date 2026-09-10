from django.contrib import admin

from .models import AccountDeletionRequest, Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted', 'granted_at')
    list_filter = ('consent_type', 'granted')
    search_fields = ('user__email',)


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'processed_at', 'reason_preview')
    search_fields = ('user__email', 'reason', 'notes')
    readonly_fields = ('created_at',)

    @admin.display(description='Powód')
    def reason_preview(self, obj):
        text = (obj.reason or '').strip()
        if len(text) <= 48:
            return text
        return f'{text[:45]}…'

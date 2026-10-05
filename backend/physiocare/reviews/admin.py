from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Panel admina dla modelu opinii fizjoterapeutów."""

    list_display = ['id', 'therapist', 'patient', 'rating', 'is_visible', 'is_anonymous', 'created_at']
    list_filter = ['rating', 'is_visible', 'is_anonymous']
    search_fields = ['therapist__user__last_name', 'patient__user__last_name', 'comment']
    readonly_fields = ['id', 'created_at', 'therapist_replied_at']
    ordering = ['-created_at']
    raw_id_fields = ['patient', 'therapist', 'visit']

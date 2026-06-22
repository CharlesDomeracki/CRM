from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "phone", "email", "status", "conversion_rating", "star_count", "contact_date", "followup_date")
    list_filter = ("status", "conversion_rating", "state", "primary_category_name")
    search_fields = ("name", "address", "city", "state", "zip", "phone", "email")
    list_editable = ("status", "conversion_rating")

from django.contrib import admin

from .models import Lead, LeadActivity


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 0
    readonly_fields = ("actor", "title", "body", "created_at")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "stage", "assigned_to", "source", "next_follow_up", "updated_at")
    list_filter = ("stage", "source", "assigned_to")
    search_fields = ("name", "phone", "email", "address", "source")
    inlines = [LeadActivityInline]


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ("lead", "title", "actor", "created_at")
    list_filter = ("title", "actor")
    search_fields = ("lead__name", "body")

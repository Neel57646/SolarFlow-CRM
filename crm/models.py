from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class LeadStage(models.TextChoices):
    NEW = "New Lead", "New Lead"
    CONTACTED = "Contacted", "Contacted"
    QUALIFIED = "Qualified", "Qualified"
    QUOTE_SENT = "Quote Sent", "Quote Sent"
    INSPECTION_BOOKED = "Inspection Booked", "Inspection Booked"
    INSTALLATION_SCHEDULED = "Installation Scheduled", "Installation Scheduled"
    COMPLETED = "Completed", "Completed"
    LOST = "Lost", "Lost"


class Lead(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_leads",
        null=True,
        blank=True,
    )
    stage = models.CharField(max_length=40, choices=LeadStage.choices, default=LeadStage.NEW)
    last_contacted = models.DateField(null=True, blank=True)
    next_follow_up = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_closed(self):
        return self.stage in {LeadStage.COMPLETED, LeadStage.LOST}

    @property
    def is_overdue(self):
        if not self.next_follow_up or self.is_closed:
            return False
        return self.next_follow_up < timezone.localdate()

    @property
    def is_stuck(self):
        if self.is_closed:
            return False
        reference = self.last_contacted or timezone.localdate(self.created_at)
        return reference <= timezone.localdate() - timedelta(days=7)

    @property
    def days_open(self):
        return (timezone.now() - self.created_at).days


class LeadActivity(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=120)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead.name}: {self.title}"

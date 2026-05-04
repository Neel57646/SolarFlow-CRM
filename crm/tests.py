from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Lead, LeadActivity, LeadStage
from .services import ensure_roles


class SolarFlowTests(TestCase):
    def setUp(self):
        ensure_roles()
        self.manager_group = Group.objects.get(name="Manager")
        self.staff_group = Group.objects.get(name="Staff")
        self.manager = User.objects.create_user(username="mia", password="demo12345", first_name="Mia")
        self.manager.groups.add(self.manager_group)
        self.staff = User.objects.create_user(username="ava", password="demo12345", first_name="Ava")
        self.staff.groups.add(self.staff_group)
        self.other_staff = User.objects.create_user(username="noah", password="demo12345", first_name="Noah")
        self.other_staff.groups.add(self.staff_group)
        self.lead = Lead.objects.create(
            name="Olivia Chen",
            phone="0401555210",
            source="CSV import",
            assigned_to=self.staff,
            stage=LeadStage.NEW,
            next_follow_up=timezone.localdate() - timedelta(days=1),
            notes="Needs quick call back.",
        )

    def test_login_required_for_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_invalid_login_rejected(self):
        response = self.client.post(reverse("login"), {"username": "mia", "password": "wrong"})
        self.assertContains(response, "Please enter a correct username and password.", status_code=200)

    def test_manager_can_view_dashboard_and_all_leads(self):
        self.client.login(username="mia", password="demo12345")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Olivia Chen")

    def test_staff_only_sees_assigned_leads(self):
        Lead.objects.create(name="Hidden Lead", phone="0400000000", source="Manual", assigned_to=self.other_staff)
        self.client.login(username="ava", password="demo12345")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Olivia Chen")
        self.assertNotContains(response, "Hidden Lead")

    def test_stage_update_creates_activity(self):
        self.client.login(username="ava", password="demo12345")
        response = self.client.post(
            reverse("lead-update", args=[self.lead.pk]),
            {
                "stage": LeadStage.QUALIFIED,
                "assigned_to": self.staff.pk,
                "last_contacted": timezone.localdate(),
                "next_follow_up": timezone.localdate(),
                "notes": self.lead.notes,
                "activity_note": "Spoke with customer and confirmed interest.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LeadActivity.objects.filter(lead=self.lead, title="Stage updated").exists())
        self.assertTrue(LeadActivity.objects.filter(lead=self.lead, title="Activity note").exists())

    def test_csv_import_creates_leads(self):
        self.client.login(username="mia", password="demo12345")
        csv_content = b"name,phone,email,address,source,stage,notes\nTest Lead,0400123456,test@example.com,Sydney,Referral,New Lead,Imported note"
        upload = SimpleUploadedFile("leads.csv", csv_content, content_type="text/csv")
        response = self.client.post(reverse("lead-import"), {"csv_file": upload})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lead.objects.filter(name="Test Lead").exists())

    def test_overdue_and_lost_filters_work(self):
        self.client.login(username="mia", password="demo12345")
        response = self.client.get(reverse("dashboard"), {"status": "overdue"})
        self.assertContains(response, "Olivia Chen")
        self.lead.stage = LeadStage.LOST
        self.lead.save()
        response = self.client.get(reverse("dashboard"), {"status": "active"})
        self.assertNotContains(response, "Olivia Chen")

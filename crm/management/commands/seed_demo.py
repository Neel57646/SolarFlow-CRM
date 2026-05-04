from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Lead, LeadStage
from crm.services import ensure_roles, log_lead_activity


class Command(BaseCommand):
    help = "Create demo users and sample solar leads."

    def handle(self, *args, **options):
        ensure_roles()
        manager_group = Group.objects.get(name="Manager")
        staff_group = Group.objects.get(name="Staff")

        users = [
            ("ava", "Ava", "Sales", "ava@example.com", "demo12345", staff_group),
            ("noah", "Noah", "Booker", "noah@example.com", "demo12345", staff_group),
            ("mia", "Mia", "Manager", "mia@example.com", "demo12345", manager_group),
        ]

        created_users = {}
        for username, first_name, last_name, email, password, group in users:
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "last_name": last_name, "email": email},
            )
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.set_password(password)
            user.save()
            user.groups.add(group)
            created_users[username] = user

        if Lead.objects.exists():
            self.stdout.write(self.style.WARNING("Leads already exist. Demo users were updated, but sample leads were not duplicated."))
            return

        leads = [
            {
                "name": "Olivia Chen",
                "phone": "0401 555 210",
                "email": "olivia.chen@example.com",
                "address": "Parramatta, NSW",
                "source": "NSW Solar Rebate List",
                "assigned_to": created_users["ava"],
                "stage": LeadStage.NEW,
                "next_follow_up": timezone.localdate(),
                "notes": "Interested in a 10kW system for family home.",
                "days_ago": 1,
            },
            {
                "name": "Liam Patel",
                "phone": "0414 823 110",
                "email": "liam.patel@example.com",
                "address": "Newcastle, NSW",
                "source": "Website form",
                "assigned_to": created_users["noah"],
                "stage": LeadStage.QUALIFIED,
                "last_contacted": timezone.localdate() - timedelta(days=1),
                "next_follow_up": timezone.localdate() + timedelta(days=2),
                "notes": "Wants financing options and battery add-on.",
                "days_ago": 5,
            },
            {
                "name": "Sophia Nguyen",
                "phone": "0423 778 654",
                "email": "sophia.nguyen@example.com",
                "address": "Wollongong, NSW",
                "source": "Referral partner",
                "assigned_to": created_users["ava"],
                "stage": LeadStage.QUOTE_SENT,
                "last_contacted": timezone.localdate() - timedelta(days=8),
                "next_follow_up": timezone.localdate() - timedelta(days=1),
                "notes": "Quote sent last week. Waiting on customer response.",
                "days_ago": 12,
            },
            {
                "name": "Ethan Brooks",
                "phone": "0430 951 246",
                "email": "ethan.brooks@example.com",
                "address": "Central Coast, NSW",
                "source": "Government energy portal",
                "assigned_to": created_users["noah"],
                "stage": LeadStage.INSTALLATION_SCHEDULED,
                "last_contacted": timezone.localdate() - timedelta(days=2),
                "next_follow_up": timezone.localdate() + timedelta(days=5),
                "notes": "Install booked for next Tuesday. Customer requested SMS reminder.",
                "days_ago": 15,
            },
        ]

        for payload in leads:
            days_ago = payload.pop("days_ago")
            lead = Lead.objects.create(**payload)
            lead.created_at = timezone.now() - timedelta(days=days_ago)
            lead.save(update_fields=["created_at"])
            log_lead_activity(lead, lead.assigned_to, "Lead created", "Seeded demo lead for SolarFlow CRM.")
            if lead.notes:
                log_lead_activity(lead, lead.assigned_to, "Initial note", lead.notes)

        self.stdout.write(self.style.SUCCESS("Demo users created: mia / ava / noah with password demo12345"))

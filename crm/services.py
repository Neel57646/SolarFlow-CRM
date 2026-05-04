from django.contrib.auth.models import Group, User

from .models import Lead, LeadActivity, LeadStage

CSV_FIELD_ALIASES = {
    "name": ("name", "customer", "customer_name"),
    "phone": ("phone", "mobile"),
    "email": ("email",),
    "address": ("address", "suburb"),
    "source": ("source", "lead_source"),
    "stage": ("stage",),
    "notes": ("notes",),
}


def ensure_roles():
    for role_name in ("Manager", "Staff"):
        Group.objects.get_or_create(name=role_name)


def user_is_manager(user):
    return user.is_authenticated and user.groups.filter(name="Manager").exists()


def visible_leads_for_user(user):
    queryset = Lead.objects.select_related("assigned_to").prefetch_related("activities")
    if user_is_manager(user):
        return queryset
    return queryset.filter(assigned_to=user)


def log_lead_activity(lead, actor, title, body):
    LeadActivity.objects.create(lead=lead, actor=actor, title=title, body=body)


def normalize_stage(value):
    if not value:
        return LeadStage.NEW
    for stage, _label in LeadStage.choices:
        if value.strip().lower() == stage.lower():
            return stage
    return LeadStage.NEW


def import_leads_from_rows(rows, actor):
    imported = 0
    skipped = []
    default_owner = actor if actor.is_authenticated else User.objects.filter(is_superuser=True).first()

    for index, row in enumerate(rows, start=2):
        normalized = {}
        lower_row = {key.strip().lower(): (value or "").strip() for key, value in row.items() if key}
        for target, aliases in CSV_FIELD_ALIASES.items():
            normalized[target] = next((lower_row.get(alias, "") for alias in aliases if lower_row.get(alias, "")), "")

        if not normalized["name"] or not normalized["phone"]:
            skipped.append(f"Row {index}: missing name or phone.")
            continue

        lead = Lead.objects.create(
            name=normalized["name"],
            phone=normalized["phone"],
            email=normalized["email"],
            address=normalized["address"],
            source=normalized["source"] or "CSV import",
            stage=normalize_stage(normalized["stage"]),
            notes=normalized["notes"],
            assigned_to=default_owner,
        )
        log_lead_activity(lead, actor, "Lead imported", f"Lead imported from CSV source: {lead.source}.")
        imported += 1

    return imported, skipped

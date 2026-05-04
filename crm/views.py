from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CSVImportForm, LeadCreateForm, LeadFilterForm, LeadUpdateForm
from .models import LeadStage
from .services import ensure_roles, import_leads_from_rows, log_lead_activity, user_is_manager, visible_leads_for_user


def home(request):
    return redirect("dashboard" if request.user.is_authenticated else "login")


@login_required
def dashboard(request):
    ensure_roles()
    manager = user_is_manager(request.user)
    lead_queryset = visible_leads_for_user(request.user)
    filter_form = LeadFilterForm(request.GET or None, user=request.user)
    create_form = LeadCreateForm(user=request.user)
    import_form = CSVImportForm()

    if filter_form.is_valid():
        stage = filter_form.cleaned_data.get("stage")
        owner = filter_form.cleaned_data.get("assigned_to")
        status = filter_form.cleaned_data.get("status") or "all"
        if stage:
            lead_queryset = lead_queryset.filter(stage=stage)
        if manager and owner:
            lead_queryset = lead_queryset.filter(assigned_to_id=owner)
        if status == "overdue":
            lead_queryset = lead_queryset.filter(next_follow_up__lt=timezone.localdate()).exclude(stage__in=[LeadStage.COMPLETED, LeadStage.LOST])
        elif status == "stuck":
            threshold = timezone.localdate() - timedelta(days=7)
            lead_queryset = lead_queryset.filter(Q(last_contacted__lte=threshold) | Q(last_contacted__isnull=True, created_at__date__lte=threshold)).exclude(stage__in=[LeadStage.COMPLETED, LeadStage.LOST])
        elif status == "active":
            lead_queryset = lead_queryset.exclude(stage__in=[LeadStage.COMPLETED, LeadStage.LOST])

    lead_queryset = lead_queryset.order_by("stage", "next_follow_up", "-created_at")

    all_visible = visible_leads_for_user(request.user)
    metrics = {
        "active": all_visible.exclude(stage__in=[LeadStage.COMPLETED, LeadStage.LOST]).count(),
        "overdue": sum(1 for lead in all_visible if lead.is_overdue),
        "stuck": sum(1 for lead in all_visible if lead.is_stuck),
        "scheduled": all_visible.filter(stage=LeadStage.INSTALLATION_SCHEDULED).count(),
    }

    stage_counts = (
        all_visible.values("stage")
        .annotate(total=Count("id"))
        .order_by()
    )
    stage_count_map = {item["stage"]: item["total"] for item in stage_counts}
    follow_up_queue = all_visible.exclude(stage__in=[LeadStage.COMPLETED, LeadStage.LOST]).order_by("next_follow_up", "-created_at")[:6]

    context = {
        "filter_form": filter_form,
        "create_form": create_form,
        "import_form": import_form,
        "leads": lead_queryset,
        "metrics": metrics,
        "stage_count_map": stage_count_map,
        "stages": LeadStage.choices,
        "follow_up_queue": follow_up_queue,
        "is_manager": manager,
    }
    return render(request, "crm/dashboard.html", context)


@login_required
def lead_create(request):
    form = LeadCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        lead = form.save()
        log_lead_activity(lead, request.user, "Lead created", "Lead created manually in SolarFlow CRM.")
        if lead.notes:
            log_lead_activity(lead, request.user, "Initial note", lead.notes)
        messages.success(request, f"{lead.name} was added to the pipeline.")
    elif request.method == "POST":
        messages.error(request, "Please fix the errors in the lead form.")
    return redirect("dashboard")


@login_required
def lead_import(request):
    if request.method != "POST":
        return redirect("dashboard")

    form = CSVImportForm(request.POST, request.FILES)
    if form.is_valid():
        imported, skipped = import_leads_from_rows(form.parse_rows(), request.user)
        if imported:
            messages.success(request, f"Imported {imported} lead(s) from CSV.")
        if skipped:
            messages.warning(request, "Some rows were skipped: " + " ".join(skipped[:5]))
    else:
        messages.error(request, "Please upload a valid CSV file.")
    return redirect("dashboard")


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(visible_leads_for_user(request.user), pk=pk)
    form = LeadUpdateForm(instance=lead, user=request.user)
    return render(
        request,
        "crm/lead_detail.html",
        {
            "lead": lead,
            "form": form,
            "is_manager": user_is_manager(request.user),
        },
    )


@login_required
def lead_update(request, pk):
    lead = get_object_or_404(visible_leads_for_user(request.user), pk=pk)
    if request.method != "POST":
        return HttpResponseRedirect(reverse("lead-detail", args=[lead.pk]))

    previous_stage = lead.stage
    previous_owner = lead.assigned_to
    form = LeadUpdateForm(request.POST, instance=lead, user=request.user)
    if form.is_valid():
        updated = form.save()
        if previous_stage != updated.stage:
            log_lead_activity(updated, request.user, "Stage updated", f"Moved from {previous_stage} to {updated.stage}.")
        if previous_owner != updated.assigned_to:
            owner_name = updated.assigned_to.get_full_name() if updated.assigned_to else "Unassigned"
            log_lead_activity(updated, request.user, "Owner updated", f"Lead reassigned to {owner_name}.")
        if form.cleaned_data.get("activity_note"):
            log_lead_activity(updated, request.user, "Activity note", form.cleaned_data["activity_note"])
        messages.success(request, "Lead details updated.")
    else:
        messages.error(request, "Please correct the form errors before saving.")
    return redirect("lead-detail", pk=lead.pk)

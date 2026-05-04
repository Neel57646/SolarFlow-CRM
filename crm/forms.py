import csv
import io

from django import forms
from django.contrib.auth.models import User

from .models import Lead, LeadStage


class LeadFilterForm(forms.Form):
    stage = forms.ChoiceField(required=False)
    assigned_to = forms.ChoiceField(required=False, label="Owner")
    status = forms.ChoiceField(
        required=False,
        choices=(
            ("all", "All leads"),
            ("overdue", "Overdue follow-up"),
            ("stuck", "Stuck over 7 days"),
            ("active", "Active only"),
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        stage_choices = [("", "All stages"), *LeadStage.choices]
        owner_choices = [("", "All owners"), *[(str(item.pk), item.get_full_name() or item.username) for item in User.objects.order_by("first_name", "username")]]
        self.fields["stage"].choices = stage_choices
        self.fields["assigned_to"].choices = owner_choices if user and user.groups.filter(name="Manager").exists() else [("", "My leads")]
        self.fields["status"].initial = "all"


class LeadCreateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "name",
            "phone",
            "email",
            "address",
            "source",
            "assigned_to",
            "stage",
            "next_follow_up",
            "notes",
        ]
        widgets = {
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        user_queryset = User.objects.order_by("first_name", "username")
        if user and not user.groups.filter(name="Manager").exists():
            user_queryset = user_queryset.filter(pk=user.pk)
            self.fields["assigned_to"].initial = user.pk
        self.fields["assigned_to"].queryset = user_queryset


class LeadUpdateForm(forms.ModelForm):
    activity_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Lead
        fields = ["stage", "assigned_to", "last_contacted", "next_follow_up", "notes"]
        widgets = {
            "last_contacted": forms.DateInput(attrs={"type": "date"}),
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        manager = user and user.groups.filter(name="Manager").exists()
        queryset = User.objects.order_by("first_name", "username")
        if not manager and user:
            queryset = queryset.filter(pk=user.pk)
            self.fields["assigned_to"].initial = user.pk
            self.fields["assigned_to"].disabled = True
        self.fields["assigned_to"].queryset = queryset


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(help_text="Upload a CSV with lead columns such as name, phone, email, address, source, stage, notes.")

    def clean_csv_file(self):
        uploaded = self.cleaned_data["csv_file"]
        if not uploaded.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a CSV file.")
        return uploaded

    def parse_rows(self):
        uploaded = self.cleaned_data["csv_file"]
        text = uploaded.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

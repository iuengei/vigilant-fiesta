from django.forms import forms
from django.forms.models import ModelForm
from achievement import models
from utils.mixins.form import FormFieldQuerysetFilterMixin


class TestForm(ModelForm):
    class Meta:
        model = models.Test
        fields = ['name', 'exam_type']


class AchievementForm(FormFieldQuerysetFilterMixin, ModelForm):
    class Meta:
        model = models.Achievement
        fields = '__all__'
        exclude = ['initiator']


class PaperForm(ModelForm):
    class Meta:
        model = models.Paper
        fields = ['name', 'subject', 'grade', 'file']

from django import forms
from django.forms import widgets
from django.forms.widgets import DateInput, TimeInput
from main import models
import accounts.models as accounts_models
from django.forms.utils import to_current_timezone
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user
from utils.mixins.form import FormM2MFieldMixin, FormFieldDisabledMixin, FormLimitChoicesMixin, FormChainMixin


class TagForm(forms.Form):
    content = forms.CharField(max_length=256, widget=forms.Textarea)
    to = forms.IntegerField(widget=forms.HiddenInput)
    author = forms.IntegerField(widget=forms.HiddenInput)


class StudentForm(FormLimitChoicesMixin,
                  FormFieldDisabledMixin,
                  FormChainMixin,
                  forms.ModelForm):
    disabled_fields = ['id_card', 'name', 'branch', 'sex']
    other_forms = {
        'parents': inlineformset_factory(models.Student, models.Parent, fields='__all__', extra=0),
    }

    class Meta:
        model = models.Student
        fields = '__all__'
        exclude = ['img', 'teachers']


class StudentAddForm(FormLimitChoicesMixin,
                     forms.ModelForm):
    other_forms = {
        'parents': inlineformset_factory(models.Student, models.Parent, fields='__all__', extra=0),
    }

    class Meta:
        model = models.Student
        fields = '__all__'
        exclude = ['img', 'teachers']


class StudentTeacherForm(FormLimitChoicesMixin,
                         FormM2MFieldMixin,
                         forms.ModelForm):
    m2m_filed = 'teachers'
    m2m_filter_args = ['grades', 'subject']
    m2m_filter_initial = {'grades': 'grade'}

    class Meta:
        model = models.Student
        fields = ['teachers']

    def clean(self):
        branch_balanced = True
        if self.cleaned_data.get('teachers') is None:
            return self.cleaned_data
        for teacher in self.cleaned_data.get('teachers'):
            if teacher.branch != self.instance.branch:
                branch_balanced = False
                self.add_error('teachers',
                               forms.ValidationError(_('student and teacher %s should in same branch.'),
                                                     code='invalid',
                                                     params=(teacher,)))
        if branch_balanced:
            return self.cleaned_data


class MyDateTimeWidget(widgets.MultiWidget):
    supports_microseconds = False
    template_name = 'django/forms/widgets/splitdatetime.html'

    def __init__(self, date_format=None, time_format=None):
        _widgets = (
            DateInput(attrs={'type': 'date'}, format=date_format),
            TimeInput(attrs={'type': 'time'}, format=time_format),
        )
        super(MyDateTimeWidget, self).__init__(_widgets)

    def decompress(self, value):
        if value:
            value = to_current_timezone(value)
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]


class TeacherForm(FormLimitChoicesMixin,
                  FormM2MFieldMixin,
                  forms.ModelForm):
    m2m_filed = 'grades'
    fields_filter = ['branch']

    class Meta:
        model = models.Teacher
        fields = '__all__'


class TeacherChangeForm(FormFieldDisabledMixin,
                        FormM2MFieldMixin,
                        forms.ModelForm):
    m2m_filed = 'grades'
    disabled_exclude = ['mobile', 'grades']

    class Meta:
        model = models.Teacher
        fields = ['sex', 'age', 'subject', 'mobile', 'grades']


class SupervisorForm(forms.ModelForm):
    branch = forms.IntegerField(widget=forms.Select)

    def __init__(self, *args, branch=0, add=True, **kwargs):
        super(SupervisorForm, self).__init__(*args, **kwargs)
        self.fields['branch'].widget.choices = [
            models.User.branch_choices[branch]] if branch else models.User.branch_choices
        if not add:
            self.fields['id_card'].disabled = True
            self.fields.pop('name')
            self.fields.pop('branch')

    class Meta:
        model = models.Supervisor
        fields = '__all__'


class InterviewForm(forms.ModelForm):
    class Meta:
        model = models.Interview
        fields = '__all__'
        exclude = ['author']

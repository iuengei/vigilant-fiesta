from django import forms
from django.forms import widgets
from django.forms.widgets import DateInput, TimeInput
from main import models
import accounts.models as accounts_models
from django.forms.utils import to_current_timezone
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user


class TagForm(forms.Form):
    content = forms.CharField(max_length=256, widget=forms.Textarea)
    to = forms.IntegerField(widget=forms.HiddenInput)
    author = forms.IntegerField(widget=forms.HiddenInput)


class StudentForm(forms.ModelForm):
    branch = forms.IntegerField(widget=forms.Select)

    def __init__(self, *args, user, add=True, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

        branch = user.branch
        self.fields['branch'].widget.choices = [
            models.User.branch_choices[branch]] if branch else models.User.branch_choices

        if branch:
            duty = user.duty
            self.fields['supervisor'] = forms.ModelChoiceField(queryset=accounts_models.Supervisor.objects.filter(
                user_info=user) if duty else accounts_models.Supervisor.objects.filter(branch=branch))

        instance = kwargs.get('instance', None)
        data = args[0] if args else None
        self.parents = inlineformset_factory(self._meta.model, models.Parent,
                                             fields='__all__', extra=0)(data, instance=instance, prefix='parents')

        if not add:
            for field in ['id_card', 'name', 'branch', 'sex']:
                self.fields[field].disabled = True

    class Meta:
        model = models.Student
        fields = '__all__'
        exclude = ['img', 'teachers']


class StudentTeacherForm(forms.ModelForm):
    filter_fields = ['grades', 'subject']

    def __init__(self, *args, **kwargs):
        super(StudentTeacherForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        branch = instance.branch
        grade = instance.grade
        self.fields['teachers'] = forms.ModelMultipleChoiceField(
            queryset=accounts_models.Teacher.objects.filter(
                branch=branch) if branch else accounts_models.Teacher.objects.all())

        self.grades = forms.IntegerField(initial=grade, widget=forms.Select(choices=models.grade_choices)).get_bound_field(self, 'grades')
        self.subject = forms.IntegerField(
            widget=forms.Select(choices=accounts_models.Teacher.subject_choices)).get_bound_field(self, 'subject')

    class Meta:
        model = models.Student
        fields = ['teachers']

    def clean(self):
        branch_balanced = True
        for teacher in self.cleaned_data.get('teachers'):
            if teacher.branch != self.instance.branch:
                branch_balanced = False
                break
        if branch_balanced:
            return self.cleaned_data
        else:
            raise forms.ValidationError('student and teachers should in same branch.')


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


class CourseChainForm(forms.ModelForm):
    def __init__(self, *args, course_plan, **kwargs):
        super(CourseChainForm, self).__init__(*args, **kwargs)

        self.fields['teacher'].queryset = course_plan.student.teachers

        data = args[0] if args else None
        self.course_plan = CoursePlanForm(data, instance=course_plan, prefix='course_plan')

    class Meta:
        model = models.CoursesRecord
        fields = '__all__'
        exclude = ['student', 'status']


class CoursePlanForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super(CoursePlanForm, self).__init__(*args, **kwargs)

        if user:
            students = get_objects_for_user(user, 'main.change_student', accept_global_perms=False)
            branch = user.branch

            self.base_fields['student'].queryset = students

            branch_disabled = True if branch else False
            self.branch = forms.IntegerField(widget=forms.Select(choices=models.branch_choices),
                                             initial=branch, disabled=branch_disabled).get_bound_field(self, 'branch')
        else:
            for name, field in self.fields.items():
                field.disabled = True

    class Meta:
        model = models.CoursePlan
        fields = '__all__'
        exclude = ['create_time', 'status']


class LessonPlanForm(forms.ModelForm):
    content = forms.CharField(min_length=246, max_length=1024, widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(LessonPlanForm, self).__init__(*args, **kwargs)

    def clean(self):
        content = self.cleaned_data.get('content')
        file = self.cleaned_data.get('file')

        if not content and not file:
            raise forms.ValidationError(_("Content and file can't both be empty."), code='invalid')

        return self.cleaned_data

    class Meta:
        model = models.LessonPlan
        fields = ['title', 'content', 'file']

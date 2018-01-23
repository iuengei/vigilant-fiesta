from django import forms
from course import models
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user


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

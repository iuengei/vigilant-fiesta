from django import forms
from course import models
from django.utils.timezone import timedelta
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
        exclude = ['student', 'status', 'lesson_timedelta']

    def clean(self):
        teacher = self.cleaned_data['teacher']
        lesson_time = self.cleaned_data['lesson_time']
        date_from = lesson_time - timedelta(seconds=3600 * 4)
        date_to = lesson_time + timedelta(seconds=self.course_plan.instance.hours * 3600)
        range_courses = teacher.coursesrecord_set.filter(lesson_time__range=(date_from, date_to))
        if range_courses:
            for course in range_courses:
                course_time = course.lesson_time
                course_over = course.lesson_time + timedelta(course.lesson_timedelta)
                if (lesson_time < course_time and date_to > course_time) or (
                                lesson_time >= course_time and lesson_time < course_over):
                    self.add_error('teacher', forms.ValidationError(_('Teacher %s had course form %s to %s.'),
                                                                    code='invalid',
                                                                    params=(teacher.name,
                                                                            course_time.strftime("%Y-%m-%d %H:%M"),
                                                                            course_over.strftime("%H:%M"))))
        if self.errors:
            return self.cleaned_data
        self.cleaned_data['lesson_timedelta'] = float(self.course_plan.instance.hours * 3600 / 86400)
        return self.cleaned_data


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

    def clean_plan_time(self):
        plan_time = self.cleaned_data.get('plan_time')
        if plan_time.minute not in [0, 30]:
            raise forms.ValidationError('Parameter plan_time should be a point or a half ', code='invalid')
        return plan_time.replace(second=0, microsecond=0)


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

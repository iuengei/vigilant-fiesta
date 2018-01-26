from django import forms
from course import models
from django.utils.timezone import timedelta
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import get_objects_for_user
from utils.mixins.form import FormChainMixin, FormLimitChoicesMixin, FormFieldDisabledMixin
from functools import partialmethod

from django.conf import settings

choices_config = settings.CHOICES_CONFIG


class CoursePlanForm(FormLimitChoicesMixin,
                     forms.ModelForm):
    branch = forms.IntegerField(widget=forms.Select(choices=choices_config.branch_choices))

    class Meta:
        model = models.CoursePlan
        fields = '__all__'
        exclude = ['create_time', 'status']

    def clean_plan_time(self):
        plan_time = self.cleaned_data.get('plan_time')
        if plan_time.minute not in [0, 30]:
            raise forms.ValidationError('Parameter plan_time should be a point or a half ', code='invalid')
        return plan_time.replace(second=0, microsecond=0)


class CoursePlanDisabledForm(FormFieldDisabledMixin,
                             forms.ModelForm):
    class Meta:
        model = models.CoursePlan
        fields = '__all__'
        exclude = ['create_time', 'status']


class CourseChainForm(FormChainMixin,
                      forms.ModelForm):
    other_forms = {
        'course_plan': CoursePlanDisabledForm,
    }

    def __init__(self, *args, **kwargs):
        course_plan = kwargs.get('course_plan')
        super(CourseChainForm, self).__init__(*args, **kwargs)

        self.fields['teacher'].queryset = course_plan.student.teachers

    class Meta:
        model = models.CoursesRecord
        fields = '__all__'
        exclude = ['plan', 'status', 'lesson_timedelta', 'lesson_plan', 'attendance']

    def clean_lesson_time(self):
        lesson_time = self.cleaned_data.get('lesson_time')
        if lesson_time.minute not in [0, 30]:
            self.add_error('lesson_time',
                           forms.ValidationError('Parameter plan_time should be a point or a half.', code='invalid'))
        if lesson_time < self.course_plan.instance.plan_time:
            self.add_error('lesson_time',
                           forms.ValidationError('Parameter lesson_time is earlier than plan_time.', code='invalid'))
        return lesson_time.replace(second=0, microsecond=0)

    def clean(self):

        teacher = self.cleaned_data['teacher']
        lesson_time = self.cleaned_data['lesson_time']
        date_from = lesson_time - timedelta(seconds=3600 * 4)  # 上课前4小时
        date_to = lesson_time + timedelta(seconds=self.course_plan.instance.hours * 3600)  # 上课结束时间

        #  (date_from ,date_to) 时间段教师其他课程安排
        range_courses = teacher.coursesrecord_set.filter(lesson_time__range=(date_from, date_to))
        if range_courses:
            for course in range_courses:
                course_time = course.lesson_time
                course_over = course.lesson_time + timedelta(course.lesson_timedelta)

                if any((
                        all((lesson_time < course_time, date_to > course_time)),
                        course_time <= lesson_time < course_over
                )):
                    self.add_error('teacher',
                                   forms.ValidationError(
                                       _('Teacher %s had course form %s to %s.'),
                                       code='invalid',
                                       params=(teacher.name,
                                               course_time.strftime("%Y-%m-%d %H:%M"),
                                               course_over.strftime("%H:%M"))))
        if self.errors:
            return self.cleaned_data
        self.cleaned_data['lesson_timedelta'] = float(self.course_plan.instance.hours * 3600 / 86400)
        return self.cleaned_data


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

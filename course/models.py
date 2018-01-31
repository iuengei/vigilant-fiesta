from django.db import models
from django.utils.timezone import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from guardian.shortcuts import assign_perm
from accounts.models import User

from django.conf import settings

choices_config = settings.CHOICES_CONFIG


class LessonPlan(models.Model):
    """教案表"""
    title = models.CharField(max_length=32)
    author = models.ForeignKey('accounts.User')
    content = models.TextField(max_length=1024, null=True, blank=True)
    file = models.FileField(upload_to='upload/LessonPlan', null=True, blank=True)

    @staticmethod
    @receiver(post_save, sender='course.LessonPlan')
    def assign_perm(sender, instance=None, created=False, **kwargs):
        if created:
            users = User.objects.filter(duty=0, branch=instance.author.branch)
            if users:
                for user in users:
                    assign_perm('course.change_lessonplan', user, instance)
            assign_perm('course.change_lessonplan', instance.author, instance)

    class Meta:
        permissions = (
            ('view_lessonplan', 'Can view lesson plan'),
        )


class CoursesRecord(models.Model):
    """课程记录表"""
    plan = models.OneToOneField('CoursePlan', verbose_name='学生')
    teacher = models.ForeignKey('main.Teacher', verbose_name='教师')
    attendance = models.SmallIntegerField(null=True, blank=True, choices=choices_config.attendance_choices,
                                          verbose_name='考勤')
    lesson_plan = models.ForeignKey('LessonPlan', null=True, blank=True, verbose_name='教案')
    lesson_time = models.DateTimeField(default=datetime.now().replace(minute=0, second=0, microsecond=0),
                                       verbose_name='上课时间')
    lesson_timedelta = models.FloatField(default=7200 / 86400, verbose_name='上课时长')
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')
    status = models.SmallIntegerField(choices=choices_config.course_status_choices, default=3, verbose_name='状态')

    @staticmethod
    @receiver(post_delete, sender='course.CoursesRecord')
    def related_plan_delete(sender, instance=None, **kwargs):
        instance.plan.delete()

    class Meta:
        permissions = (
            ('view_coursesrecord', 'Can view courses record'),
        )

    def status_delete(self):
        self.status = 2
        self.save()

    def status_reschedule(self):
        self.status = 4
        self.save()

    def action(self, type):
        switcher = {
            'delete': self.status_delete,
            'reschedule': self.status_reschedule
        }
        return switcher[type]()


class CoursePlan(models.Model):
    """课程计划表"""
    student = models.ForeignKey('main.Student', verbose_name='学生')
    grade = models.SmallIntegerField(choices=choices_config.grade_choices, verbose_name='年级')
    subject = models.SmallIntegerField(choices=choices_config.subject_choices, verbose_name='科目')
    plan_time = models.DateTimeField(default=datetime.now().replace(minute=0, second=0, microsecond=0),
                                     verbose_name='计划时间')
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')
    hours = models.SmallIntegerField(default=2, choices=[(1, '一小时'), (2, '二小时'), (3, '三小时'), (4, '四小时')],
                                     verbose_name='课时')
    status = models.BooleanField(default=False, verbose_name='完成')

    class Meta:
        permissions = (
            ('view_courseplan', 'Can view course plan'),
        )

        unique_together = ['student', 'subject', 'plan_time']

    def __str__(self):
        return '<' + self.get_grade_display() + '>' + self.student.name

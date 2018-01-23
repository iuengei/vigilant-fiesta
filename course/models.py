from django.db import models
from django.utils.timezone import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from guardian.shortcuts import assign_perm
from accounts.models import User

branch_choices = [(1, '郑大校区'),
                  (2, '省实验校区'),
                  (3, '未来路校区'),
                  (4, '洛阳校区'),
                  (5, '碧沙岗校区'),
                  (6, '郑东校区'),
                  (7, '北环校区'),
                  (8, '外国语校区')]
subject_choices = [(1, '语文'),
                   (2, '数学'),
                   (3, '英语'),
                   (4, '物理'),
                   (5, '化学'),
                   (6, '生物'),
                   (7, '历史'),
                   (8, '地理'),
                   (9, '政治')]
sex_choices = [(0, '女'), (1, '男')]
attendance_choices = [(0, '正常'),
                      (1, '老师缺席'),
                      (2, '学生缺席'),
                      (3, '老师迟到'),
                      (4, '学生迟到'),
                      (5, '老师请假'),
                      (6, '学生请假')]
grade_choices = [(1, '小一'),
                 (2, '小二'),
                 (3, '小三'),
                 (4, '小四'),
                 (5, '小五'),
                 (6, '小六'),
                 (7, '初一'),
                 (8, '初二'),
                 (9, '初三'),
                 (10, '高一'),
                 (11, '高二'),
                 (12, '高三')]
course_status_choices = ((1, 'finished'), (2, 'deleted'), (3, 'waiting'), (4, 'reschedule'))


class LessonPlan(models.Model):
    """教案表"""
    title = models.CharField(max_length=32)
    author = models.ForeignKey('accounts.User', to_field='teacher_info')
    content = models.TextField(max_length=1024, null=True, blank=True)
    file = models.FileField(upload_to='upload/LessonPlan', null=True, blank=True)

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
    student = models.OneToOneField('CoursePlan', verbose_name='学生')
    teacher = models.ForeignKey('main.Teacher', verbose_name='教师')
    attendance = models.SmallIntegerField(null=True, blank=True, choices=attendance_choices, verbose_name='考勤')
    lesson_plan = models.ForeignKey('LessonPlan', null=True, blank=True, verbose_name='教案')
    lesson_time = models.DateTimeField(default=datetime.now(), verbose_name='上课时间')
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')
    status = models.SmallIntegerField(choices=course_status_choices, default=3, verbose_name='状态')

    @receiver(post_delete, sender='course.CoursesRecord')
    def related_plan_delete(sender, instance=None, **kwargs):
        instance.student.delete()

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
    grade = models.SmallIntegerField(choices=grade_choices, verbose_name='年级')
    subject = models.SmallIntegerField(choices=subject_choices, verbose_name='科目')
    plan_time = models.DateTimeField(default=datetime.now(), verbose_name='计划时间')
    create_time = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')
    hours = models.SmallIntegerField(default=2, verbose_name='课时')
    status = models.BooleanField(default=False, verbose_name='完成')

    class Meta:
        permissions = (
            ('view_courseplan', 'Can view course plan'),
        )

    def __str__(self):
        return '<' + self.get_grade_display() + '>' + self.student.name

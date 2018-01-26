from django.db import models
from django.utils.timezone import datetime

from django.conf import settings

choices_config = settings.CHOICES_CONFIG


# Create your models here.


class Achievement(models.Model):
    student = models.ForeignKey('main.Student', related_name='tests', verbose_name='学生')
    score = models.PositiveSmallIntegerField(verbose_name='分数')
    exam = models.ForeignKey('Test', verbose_name='测验')
    exam_paper = models.ForeignKey('Paper', verbose_name='试卷')
    exam_time = models.DateTimeField(verbose_name='测试时间', default=datetime.now())
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    initiator = models.ForeignKey('accounts.User', verbose_name='发起人')

    class Meta:
        unique_together = ['student', 'exam', 'exam_paper']
        permissions = (
            ('view_achievement', 'Can view achievement'),
        )


class Test(models.Model):
    name = models.CharField(max_length=32, verbose_name='名称')
    exam_type = models.PositiveIntegerField(choices=choices_config.exam_type_choices, verbose_name='类别')

    branch = models.PositiveIntegerField(choices=choices_config.branch_choices)
    initiator = models.ForeignKey('accounts.User', verbose_name='发起人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return '(' + self.get_exam_type_display() + ')' + self.name

    class Meta:
        unique_together = ['initiator', 'name']
        permissions = (
            ('view_test', 'Can view test'),
        )

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        duty = user.duty
        if user.is_superuser:
            return queryset
        return queryset.filter(initiator=user) if duty else queryset.filter(branch=branch)


class Paper(models.Model):
    name = models.CharField(max_length=32, verbose_name='名称')
    subject = models.PositiveSmallIntegerField(choices=choices_config.subject_choices, verbose_name='学科')
    grade = models.PositiveIntegerField(choices=choices_config.grade_choices, verbose_name='年级')
    file = models.FileField(upload_to='upload/test/papers', null=True, blank=True)
    branch = models.PositiveIntegerField(choices=choices_config.branch_choices)
    author = models.ForeignKey('accounts.User', verbose_name='上传者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name + '(' + self.get_subject_display() + '|' + self.get_grade_display() + ')'

    class Meta:
        unique_together = ['author', 'name']
        permissions = (
            ('view_paper', 'Can view paper'),
        )

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        duty = user.duty
        if user.is_superuser:
            return queryset
        return queryset.filter(author=user) if duty else queryset.filter(branch=branch)

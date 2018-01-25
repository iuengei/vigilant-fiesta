from django.db import models
from django.utils.timezone import datetime

# Create your models here.
subject_choices = [(1, '语文'),
                   (2, '数学'),
                   (3, '英语'),
                   (4, '物理'),
                   (5, '化学'),
                   (6, '生物'),
                   (7, '历史'),
                   (8, '地理'),
                   (9, '政治')]
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
exam_type_choices = [(0, '周测'), (1, '月考'), (2, '期中'), (3, '期末'), (4, '其它')]
branch_choices = [(0, '郑州大区'),
                  (1, '郑大校区'),
                  (2, '省实验校区'),
                  (3, '未来路校区'),
                  (4, '洛阳校区'),
                  (5, '碧沙岗校区'),
                  (6, '郑东校区'),
                  (7, '北环校区'),
                  (8, '外国语校区')]


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
    exam_type = models.PositiveIntegerField(choices=exam_type_choices, verbose_name='类别')

    branch = models.PositiveIntegerField(choices=branch_choices)
    initiator = models.ForeignKey('accounts.User', verbose_name='发起人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return '(' + self.get_exam_type_display() + ')' + self.name

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
    subject = models.PositiveSmallIntegerField(choices=subject_choices, verbose_name='学科')
    grade = models.PositiveIntegerField(choices=grade_choices, verbose_name='年级')
    file = models.FileField(upload_to='upload/test/papers', null=True, blank=True)
    branch = models.PositiveIntegerField(choices=branch_choices)
    author = models.ForeignKey('accounts.User', verbose_name='发起人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name + '(' + self.get_subject_display() + '|' + self.get_grade_display() + ')'

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        duty = user.duty
        if user.is_superuser:
            return queryset
        return queryset.filter(author=user) if duty else queryset.filter(branch=branch)

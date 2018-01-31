from django.db import models
from django.utils.timezone import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete
from guardian.shortcuts import assign_perm, get_objects_for_user
from accounts.models import User, Group

from django.conf import settings

choices_config = settings.CHOICES_CONFIG


# Create your models here.

class Teacher(models.Model):
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=32, verbose_name='姓名')
    sex = models.SmallIntegerField(choices=choices_config.sex_choices, verbose_name='性别')
    age = models.PositiveSmallIntegerField(verbose_name='年龄')
    branch = models.SmallIntegerField(choices=choices_config.branch_choices, verbose_name='校区')
    work_type = models.IntegerField(choices=[(1, '专职'), (0, '兼职')], verbose_name='类别')
    grades = models.ManyToManyField('main.Grade', verbose_name='辅导年级')
    subject = models.SmallIntegerField(choices=choices_config.subject_choices, verbose_name='学科')
    mobile = models.CharField(max_length=32, null=True, blank=True, verbose_name='电话')

    class Meta:
        permissions = (
            ('view_teacher', 'Can view teacher'),
        )

    def __str__(self):
        return '<' + self.get_subject_display() + '>' + self.name

    def get_str(self, field):
        for each in self._meta.many_to_many:
            if field == each.name:
                _dict = {each.related_query_name(): self.id}
                _list = list(each.related_model.objects.filter(**_dict).values_list('id', flat=True))
                return '-'.join([str(i) for i in _list])

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(branch=branch)


class Supervisor(models.Model):
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=32)
    sex = models.SmallIntegerField(choices=choices_config.sex_choices)
    age = models.SmallIntegerField()

    branch = models.SmallIntegerField(choices=choices_config.branch_choices, verbose_name='校区')
    mobile = models.CharField(max_length=32)

    class Meta:
        permissions = (
            ('view_supervisor', 'Can view supervisor'),
        )

    def __str__(self):
        return self.name

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        duty = user.duty
        if user.is_superuser:
            return queryset
        if duty:
            return queryset.filter(user_info=user)
        else:
            return queryset.filter(branch=branch)


class Grade(models.Model):
    id = models.SmallIntegerField(choices=choices_config.grade_choices, primary_key=True)

    def __str__(self):
        return self.get_id_display()

    @classmethod
    def perm_queryset(cls, queryset, user):
        return queryset


class Interview(models.Model):
    """面试登记表"""
    name = models.CharField(max_length=32, verbose_name='姓名')
    sex = models.IntegerField(choices=choices_config.sex_choices, verbose_name='性别')
    age = models.IntegerField(verbose_name='年龄')
    address = models.CharField(max_length=32, verbose_name='住址')
    subject = models.SmallIntegerField(choices=choices_config.subject_choices, verbose_name='学科')
    grade_range = models.SmallIntegerField(choices=[(0, '小学'), (1, '初中'), (2, '高中')], verbose_name='年级段')
    mobile = models.CharField(max_length=32, null=True, blank=True, verbose_name='电话')
    level = models.IntegerField(choices=[(3, '优秀'), (2, '普通'), (1, '一般')], verbose_name='水平')
    result = models.IntegerField(choices=[(1, '通过'), (0, '未通过')], verbose_name='结果')
    author = models.ForeignKey('accounts.User', verbose_name='面试人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    branch = models.PositiveSmallIntegerField(choices=choices_config.branch_choices, verbose_name='校区')

    class Meta:
        permissions = (
            ('view_interview', 'Can view interview'),
        )


class Tag(models.Model):
    """标签表"""
    content = models.CharField(max_length=256)
    to = models.ForeignKey('Student')
    create_time = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey('accounts.User')

    @receiver(post_save, sender='main.Tag')
    def assign_perm(sender, instance=None, created=False, **kwargs):
        if created:
            users = User.objects.filter(duty=0, branch=instance.author.branch)
            if users:
                for user in users:
                    assign_perm('main.change_tag', user, instance)
            assign_perm('main.change_tag', instance.author, instance)

    class Meta:
        permissions = (
            ('view_tag', 'Can view tag'),
        )


class Student(models.Model):
    """学生信息表"""
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=32, verbose_name='姓名')
    sex = models.SmallIntegerField(choices=choices_config.sex_choices, verbose_name='性别')
    branch = models.SmallIntegerField(choices=choices_config.branch_choices, verbose_name='校区')
    grade = models.SmallIntegerField(choices=choices_config.grade_choices, verbose_name='年级')
    teachers = models.ManyToManyField('Teacher', verbose_name='授课教师')
    supervisor = models.ForeignKey('Supervisor', verbose_name='班主任')
    img = models.ImageField(upload_to='upload/Gravatar/student', null=True, blank=True)

    @classmethod
    def perm_queryset(cls, queryset, user):
        if queryset.model is not cls:
            raise TypeError('The model of queryset should be %s' % cls)
        branch = user.branch
        duty = user.duty
        if user.is_superuser:
            return queryset
        if duty:
            perms = ['main.change_student']
            return get_objects_for_user(user=user, perms=perms, klass=queryset, accept_global_perms=False)
        else:
            return queryset.filter(branch=branch)

    @staticmethod
    @receiver(post_save, sender='main.Student')
    def assign_perm(sender, instance=None, created=False, **kwargs):
        if created:
            supervisor = instance.supervisor.user_info
            assign_perm('change_student', supervisor, instance)
            assign_perm('change_student', Group.objects.get(name='User_' + str(instance.branch)), instance)

    class Meta:
        verbose_name = '学生信息'
        permissions = (
            ('view_student', 'Can view student'),
        )

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        if self.img == '':
            return ''
        return self.img.url


class Parent(models.Model):
    """家长表"""
    name = models.CharField(max_length=32, verbose_name='姓名')
    sex = models.SmallIntegerField(choices=[(1, '父亲'), (0, '母亲')], verbose_name='关系')
    mobile = models.CharField(max_length=32, verbose_name='联系方式')
    child = models.ForeignKey('Student', related_name='parents')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '家长信息'

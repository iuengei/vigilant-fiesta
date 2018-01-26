from __future__ import absolute_import

from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm
from guardian.core import ObjectPermissionChecker
from guardian.mixins import GuardianUserMixin

from django.conf import settings

choices_config = settings.CHOICES_CONFIG

# class Singleton(object):
#     def __new__(cls, *args, **kwargs):
#         if not hasattr(cls, '_instance'):
#             orig = super(Singleton, cls)
#             cls._instance = orig.__new__(cls)
#         return cls._instance
#
#
# class PermissionCheckerSingleton(Singleton):
#     _data = {}
#
#     def __init__(self, user):
#         self.user = user
#
#     @property
#     def core(self):
#         if self.user.pk not in self._data:
#             self._data[self.user.pk] = ObjectPermissionChecker(self.user)
#         return self._data[self.user.pk]
#
#     @core.setter
#     def core(self, value):
#         if isinstance(value, ObjectPermissionChecker):
#             self._data[self.user.pk] = value
#         else:
#             raise Exception('Parameter should be instance of ObjectPermissionChecker.')
#
#     @core.deleter
#     def core(self):
#         del self._data[self.user.pk]
#
#     def has_perm(self, perms, obj):
#         if self.user.is_superuser:
#             return True
#         elif isinstance(perms, list):
#             return any(self.core.has_perm(perm, obj) for perm in perms)
#         elif isinstance(perms, str):
#             return self.core.has_perm(perms, obj)
#         raise Exception('Parameter perm should be list or str.')
#
#     def __getattr__(self, item):
#         return getattr(self.core, item)


class PermissionCached(type):
    def __init__(cls, *args, **kwargs):
        super(PermissionCached, cls).__init__(*args, **kwargs)
        cls.__cache = {}

    def __call__(cls, user):
        user = user if user.pk else 'Anonymous'
        if user in cls.__cache:
            return cls.__cache[user]
        else:
            obj = super().__call__(user)
            cls.__cache[user] = obj
            return obj


class PermissionChecker(metaclass=PermissionCached):
    def __init__(self, user):
        self.user = user
        self._core = None

    @property
    def core(self):
        if self._core is None:
            self._core = ObjectPermissionChecker(self.user)
        return self._core

    @core.setter
    def core(self, value):
        if isinstance(value, ObjectPermissionChecker):
            self._core = value
        else:
            raise Exception('Parameter should be instance of ObjectPermissionChecker.')

    @core.deleter
    def core(self):
        self._core = None

    def __getattr__(self, item):
        return getattr(self.core, item)


# 自定义用户表
class UserProfileManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email,
                                password=password,
                                name=name
                                )
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, GuardianUserMixin, PermissionsMixin):
    email = models.EmailField(
        verbose_name='邮箱',
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=32, verbose_name='姓名')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    duty = models.SmallIntegerField(default=1, choices=choices_config.duty_choices, verbose_name='职位')

    branch_choices = choices_config.center_choice + choices_config.branch_choices
    branch = models.SmallIntegerField(default=1, choices=branch_choices, verbose_name='校区')

    teacher_info = models.OneToOneField('main.Teacher', null=True, blank=True,
                                        related_name='user_info', verbose_name='关联教师')
    supervisor_info = models.OneToOneField('main.Supervisor', null=True, blank=True,
                                           related_name='user_info', verbose_name='关联教务')

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.perm_obj = PermissionChecker(self)

    def can(self, perms, obj):
        if self.is_superuser:
            return True
        elif isinstance(perms, list):
            return any(self.perm_obj.core.has_perm(perm, obj) for perm in perms)
        elif isinstance(perms, str):
            return self.perm_obj.core.has_perm(perms, obj)
        raise Exception('Parameter perm should be list or str.')

    class Meta:
        permissions = (
            ('view_user', 'Can view user'),
        )

    def get_full_name(self):
        return self.get_branch_display() + self.get_duty_display() + ':' + self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_admin

    @staticmethod
    def get_teachers():
        return User.objects.filter(duty=2)

    @staticmethod
    def get_supervisors():
        return User.objects.filter(duty=1)

    @staticmethod
    @receiver(post_save, sender='main.Teacher')
    def create_teacher_account(instance=None, created=False, update_fields=None, **kwargs):
        update_fields = update_fields if update_fields else []
        if created and instance.work_type == 1:

            email = instance.id_card[-6:] + '@jinghan.com'
            user = User.objects.create_user(email, instance.name, email)
            user.duty = 2
            user.branch = instance.branch
            user.teacher_info = instance
            user.save()

            user.groups.add(Group.objects.get(name='Teacher'))
            assign_perm('change_teacher', Group.objects.get(name='User_' + str(instance.branch)), instance)
            assign_perm('view_teacher', Group.objects.get(name='User_' + str(instance.branch)), instance)
        elif instance.work_type == 1 and 'work_type' in update_fields:
            email = instance.id_card[-6:] + '@jinghan.com'
            try:
                user = User.objects.get(teacher_info=instance)
                user.is_active = True
                user.save()
            except User.DoesNotExist:
                user = User.objects.create_user(email, instance.name, email)
                user.duty = 2
                user.branch = instance.branch
                user.teacher_info = instance
                user.save()
        elif 'work_type' in update_fields:
            user = User.objects.get(teacher_info=instance)
            user.is_active = False
            user.save()

    @staticmethod
    @receiver(post_save, sender='main.Supervisor')
    def create_supervisor_account(instance=None, created=False, **kwargs):
        if created:
            email = instance.id_card[-6:] + '@jinghan.com'
            user = User.objects.create_user(email, instance.name, email)
            user.duty = 1
            user.branch = instance.branch
            user.supervisor_info = instance
            user.save()

            user.groups.add(Group.objects.get(name='Supervisor'))
            assign_perm('view_supervisor', Group.objects.get(name='User_' + str(instance.branch)), instance)

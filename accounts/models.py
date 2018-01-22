#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.db import models
from .auth import User


# Create your models here.
class Teacher(models.Model):
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
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=32, verbose_name='姓名')
    sex = models.SmallIntegerField(choices=sex_choices, verbose_name='性别')
    age = models.PositiveSmallIntegerField(verbose_name='年龄')
    branch = models.SmallIntegerField(choices=branch_choices, verbose_name='校区')
    work_type = models.IntegerField(choices=[(1, '专职'), (0, '兼职')], verbose_name='类别')
    grades = models.ManyToManyField('main.Grade', verbose_name='辅导年级')
    subject = models.SmallIntegerField(choices=subject_choices, verbose_name='学科')
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


class Supervisor(models.Model):
    sex_choices = [(0, '女'), (1, '男')]
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=32)
    sex = models.SmallIntegerField(choices=sex_choices)
    age = models.SmallIntegerField()
    branch_choices = [(1, '郑大校区'),
                      (2, '省实验校区'),
                      (3, '未来路校区'),
                      (4, '洛阳校区'),
                      (5, '碧沙岗校区'),
                      (6, '郑东校区'),
                      (7, '北环校区'),
                      (8, '外国语校区')]
    branch = models.SmallIntegerField(choices=branch_choices, verbose_name='校区')
    mobile = models.CharField(max_length=32)

    class Meta:
        permissions = (
            ('view_supervisor', 'Can view supervisor'),
        )

    def __str__(self):
        return self.name

# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-14 18:07
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoursePlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.SmallIntegerField(choices=[(1, '小一'), (2, '小二'), (3, '小三'), (4, '小四'), (5, '小五'), (6, '小六'), (7, '初一'), (8, '初二'), (9, '初三'), (10, '高一'), (11, '高二'), (12, '高三')], verbose_name='年级')),
                ('subject', models.SmallIntegerField(choices=[(1, '语文'), (2, '数学'), (3, '英语'), (4, '物理'), (5, '化学'), (6, '生物'), (7, '历史'), (8, '地理'), (9, '政治')], verbose_name='科目')),
                ('plan_time', models.DateTimeField(default=datetime.datetime(2018, 1, 15, 2, 7, 13, 717973), verbose_name='计划时间')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('hours', models.SmallIntegerField(default=2, verbose_name='课时')),
                ('status', models.BooleanField(default=False, verbose_name='完成')),
            ],
            options={
                'permissions': (('view_courseplan', 'Can view course plan'),),
            },
        ),
        migrations.CreateModel(
            name='CoursesRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attendance', models.SmallIntegerField(blank=True, choices=[(0, '正常'), (1, '老师缺席'), (2, '学生缺席'), (3, '老师迟到'), (4, '学生迟到'), (5, '老师请假'), (6, '学生请假')], null=True, verbose_name='考勤')),
                ('lesson_time', models.DateTimeField(default=datetime.datetime(2018, 1, 15, 2, 7, 13, 716473), verbose_name='上课时间')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('status', models.SmallIntegerField(choices=[(1, 'finished'), (2, 'deleted'), (3, 'waiting'), (4, 'reschedule')], default=3, verbose_name='状态')),
            ],
            options={
                'permissions': (('view_coursesrecord', 'Can view courses record'),),
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.SmallIntegerField(choices=[(1, '小一'), (2, '小二'), (3, '小三'), (4, '小四'), (5, '小五'), (6, '小六'), (7, '初一'), (8, '初二'), (9, '初三'), (10, '高一'), (11, '高二'), (12, '高三')], primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='姓名')),
                ('sex', models.IntegerField(choices=[(0, '女'), (1, '男')], verbose_name='性别')),
                ('age', models.IntegerField(verbose_name='年龄')),
                ('address', models.CharField(max_length=32, verbose_name='地址')),
                ('subject', models.SmallIntegerField(choices=[(1, '语文'), (2, '数学'), (3, '英语'), (4, '物理'), (5, '化学'), (6, '生物'), (7, '历史'), (8, '地理'), (9, '政治')], verbose_name='学科')),
                ('mobile', models.CharField(blank=True, max_length=32, null=True)),
                ('level', models.IntegerField(choices=[(3, '优秀'), (2, '普通'), (1, '一般')], verbose_name='水平')),
                ('result', models.IntegerField(choices=[(1, '通过'), (0, '未通过')], verbose_name='结果')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='面试人')),
                ('grade', models.ManyToManyField(to='main.Grade', verbose_name='年级')),
            ],
            options={
                'permissions': (('view_interview', 'Can view interview'),),
            },
        ),
        migrations.CreateModel(
            name='LessonPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=32)),
                ('content', models.TextField(blank=True, max_length=1024, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='upload/LessonPlan')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='teacher_info')),
            ],
            options={
                'permissions': (('view_lessonplan', 'Can view lesson plan'),),
            },
        ),
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='姓名')),
                ('sex', models.SmallIntegerField(choices=[(1, '父亲'), (0, '母亲')], verbose_name='关系')),
                ('mobile', models.CharField(max_length=32, verbose_name='联系方式')),
            ],
            options={
                'verbose_name': '家长信息',
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_card', models.CharField(max_length=18, unique=True, verbose_name='身份证号')),
                ('name', models.CharField(max_length=32, verbose_name='姓名')),
                ('sex', models.SmallIntegerField(choices=[(0, '女'), (1, '男')], verbose_name='性别')),
                ('branch', models.SmallIntegerField(choices=[(1, '郑大校区'), (2, '省实验校区'), (3, '未来路校区'), (4, '洛阳校区'), (5, '碧沙岗校区'), (6, '郑东校区'), (7, '北环校区'), (8, '外国语校区')], verbose_name='校区')),
                ('grade', models.SmallIntegerField(choices=[(1, '小一'), (2, '小二'), (3, '小三'), (4, '小四'), (5, '小五'), (6, '小六'), (7, '初一'), (8, '初二'), (9, '初三'), (10, '高一'), (11, '高二'), (12, '高三')], verbose_name='年级')),
                ('img', models.ImageField(blank=True, null=True, upload_to='upload/Gravatar/student')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Supervisor', verbose_name='班主任')),
                ('teachers', models.ManyToManyField(blank=True, null=True, to='accounts.Teacher', verbose_name='授课教师')),
            ],
            options={
                'verbose_name': '学生信息',
                'permissions': (('view_student', 'Can view student'),),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=256)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Student')),
            ],
            options={
                'permissions': (('view_tag', 'Can view tag'),),
            },
        ),
        migrations.AddField(
            model_name='parent',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parents', to='main.Student'),
        ),
        migrations.AddField(
            model_name='coursesrecord',
            name='lesson_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.LessonPlan', verbose_name='教案'),
        ),
        migrations.AddField(
            model_name='coursesrecord',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.CoursePlan', verbose_name='学生'),
        ),
        migrations.AddField(
            model_name='coursesrecord',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Teacher', verbose_name='教师'),
        ),
        migrations.AddField(
            model_name='courseplan',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Student', verbose_name='学生'),
        ),
    ]

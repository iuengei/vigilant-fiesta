#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.sitemaps.views import sitemap
from . import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='home'),
    url(r'^students/$', views.StudentsView.as_view(), name='students'),
    url(r'^students/(?P<pk>(-)?[0-9]+)/$', views.StudentView.as_view(), name='student'),
    url(r'^students/add/$', views.StudentAddView.as_view(), name='student_add'),
    url(r'^students/(?P<pk>(-)?[0-9]+)/change/$', views.StudentChangeView.as_view(), name='student_edit'),
    url(r'^students/(?P<pk>(-)?[0-9]+)/teachers/$', views.StudentTeacherView.as_view(), name='student_teacher_edit'),

    url(r'^supervisors/add/$', views.SupervisorAddView.as_view(), name='supervisor_add'),
    url(r'^teachers/add/$', views.TeacherAddView.as_view(), name='teacher_add'),

    url(r'^teachers/(?P<pk>(-)?[0-9]+)/change/$', views.TeacherChangeView.as_view(), name='teacher_edit'),
    url(r'^teachers/$', views.TeachersView.as_view(), name='teachers'),

    url(r'tags/add/(?P<to>(-)?[0-9]+)/(?P<author>(-)?[0-9]+)/$', views.TagView.as_view(), name='tag_add'),

    url(r'^interviews/$', views.InterviewsView.as_view(), name='interviews'),

    url(r'interviews/add/$', views.InterviewAddView.as_view(), name='interview_add'),

]

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

    url(r'tags/add/(?P<to>(-)?[0-9]+)/(?P<author>(-)?[0-9]+)/$', views.TagView.as_view(), name='tag_add'),

    url(r'^courses/$', views.CoursesView.as_view(), name='courses'),
    url(r'^courses/plan$', views.CoursePlanView.as_view(), name='course_plan'),
    url(r'^courses/plan/data$', views.get_plan_ajax, name='get_plan_ajax'),

    url(r'^courses/plan/delete/$', views.CoursePlanDeleteView.as_view(), name='courseplan_delete'),

    url(r'^courses/plan/(?P<pk>(-)?[0-9]+)/chain$', views.CourseChainView.as_view(), name='course_chain'),
    url(r'^courses/chain/(?P<pk>(-)?[0-9]+)/change$', views.CourseChangeView.as_view(), name='course_change'),

    url(r'^lessonplans/$', views.LessonPlanView.as_view(), name='lessonplans'),
    url(r'^lessonplans/add/$', views.LessonPlanAddView.as_view(), name='lessonplan_add'),
    url(r'^lessonplans/(?P<pk>(-)?[0-9]+)/change/$', views.LessonPlanChangeView.as_view(), name='lessonplan_edit'),

    url(r'^test$', views.test1),
]

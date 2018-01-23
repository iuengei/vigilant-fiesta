#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.contrib.sitemaps.views import sitemap
from . import views

urlpatterns = [
    url(r'^$', views.CoursesView.as_view(), name='list'),
    url(r'^plan$', views.CoursePlanView.as_view(), name='plan'),
    url(r'^plan/data$', views.get_plan_ajax, name='get_plan_ajax'),

    url(r'^plan/delete/$', views.CoursePlanDeleteView.as_view(), name='plan_delete'),

    url(r'^plan/(?P<pk>(-)?[0-9]+)/chain$', views.CourseChainView.as_view(), name='chain'),
    url(r'^chain/(?P<pk>(-)?[0-9]+)/change$', views.CourseChangeView.as_view(), name='course_edit'),

    url(r'^lessonplans/$', views.LessonPlanView.as_view(), name='lessonplans'),
    url(r'^lessonplans/add/$', views.LessonPlanAddView.as_view(), name='lessonplan_add'),
    url(r'^lessonplans/(?P<pk>(-)?[0-9]+)/change/$', views.LessonPlanChangeView.as_view(), name='lessonplan_edit'),

    url(r'^test$', views.test1),
]

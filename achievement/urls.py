#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.AchievementsView.as_view(), name='list'),
    url(r'^tests$', views.TestsView.as_view(), name='tests'),
    url(r'^papers$', views.PapersView.as_view(), name='papers'),

    url(r'^add$', views.AchievementAddView.as_view(), name='achievement_add'),
    url(r'^tests/add$', views.TestAddView.as_view(), name='test_add'),
    url(r'^papers/add$', views.PaperAddView.as_view(), name='paper_add'),

    # url(r'^plan/delete/$', views.CoursePlanDeleteView.as_view(), name='plan_delete'),
    #
    # url(r'^plan/(?P<pk>(-)?[0-9]+)/chain$', views.CourseChainView.as_view(), name='chain'),
    # url(r'^chain/(?P<pk>(-)?[0-9]+)/change$', views.CourseChangeView.as_view(), name='course_edit'),

]

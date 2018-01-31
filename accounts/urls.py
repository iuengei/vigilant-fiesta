from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^profile/teacher/$', views.TeacherInfoView.as_view(), name='teacher_info'),
    url(r'^profile/supervisor/$', views.SupervisorInfoView.as_view(), name='supervisor_info'),
    url(r'^profile/password/$', views.ChangePasswordView.as_view(), name='change_password'),

    url(r'^users/$', views.UsersView.as_view(), name='users'),
    url(r'^users/(?P<pk>(-)?[0-9]+)/$', views.UserView.as_view(), name='user'),
    url(r'^users/(?P<pk>(-)?[0-9]+)/change/$', views.UserChangeView.as_view(), name='user_edit'),
    url(r'^register/$', views.RegisterView.as_view(), name='user_add'),

    url(r'^groups/$', views.GroupsView.as_view(), name='groups'),
    url(r'^groups/(?P<group_id>[0-9]+)/users/$', views.UsersView.as_view(), name='group_users'),
    url(r'^groups/(?P<pk>(-)?[0-9]+)/$', views.GroupView.as_view(), name='group'),
    url(r'^groups/(?P<pk>(-)?[0-9]+)/change$', views.GroupChangeView.as_view(), name='group_edit'),
    url(r'^groups/add$', views.GroupAddView.as_view(), name='group_add'),

    url(r'^check_code/', views.check_code),
    url(r'^upload/(?P<img_type>(\w)+)/(?P<obj_type>(\w)+)/$', views.upload, name='upload'),
]

urlpatterns += [
    url(r'^objperms/group/(?P<pk>(-)?[0-9]+)/$', views.GroupPermsView.as_view(), kwargs={'app_label': 'main',
                                                                                         'model_name': 'student'},
        name='group_perms_default'),

    url(r'^objperms/user/(?P<pk>(-)?[0-9]+)/$', views.UserPermsView.as_view(), kwargs={'app_label': 'main',
                                                                                       'model_name': 'student'},
        name='user_perms_default'),

    url(r'^objperms/(?P<app_label>(\w)+)/(?P<model_name>(\w)+)/group/(?P<pk>(-)?[0-9]+)/$',
        views.GroupPermsView.as_view(),
        name='group_perms'),
    url(r'^objperms/(?P<app_label>(\w)+)/(?P<model_name>(\w)+)/user/(?P<pk>(-)?[0-9]+)/$',
        views.UserPermsView.as_view(),
        name='user_perms'),

    url(r'^objperms/(?P<app_label>(\w)+)/(?P<model_name>(\w)+)/(?P<pk>(-)?[0-9]+)/user/(?P<user_pk>(-)?[0-9]+)/$',
        views.UserObjPermView.as_view(),
        name='user_obj'),

    url(r'^objperms/(?P<app_label>(\w)+)/(?P<model_name>(\w)+)/(?P<pk>(-)?[0-9]+)/group/(?P<group_pk>(-)?[0-9]+)/$',
        views.GroupObjPermView.as_view(),
        name='group_obj'),

]

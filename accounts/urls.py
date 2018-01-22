from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    url(r'^profile/teacher/$', views.TeacherInfoView.as_view(), name='teacher_info'),
    url(r'^profile/supervisor/$', views.SupervisorInfoView.as_view(), name='supervisor_info'),
    url(r'^profile/password/$', views.ChangePasswordView.as_view(), name='change_password'),

    url(r'^supervisors/add/$', views.SupervisorAddView.as_view(), name='supervisor_add'),
    url(r'^teachers/add/$', views.TeacherAddView.as_view(), name='teacher_add'),

    url(r'^teachers/(?P<pk>(-)?[0-9]+)/change/$', views.TeacherChangeView.as_view(), name='teacher_edit'),
    url(r'^teachers/$', views.TeachersView.as_view(), name='teachers'),

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

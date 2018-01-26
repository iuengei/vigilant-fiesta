#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from django.http import Http404, HttpResponseForbidden, JsonResponse, StreamingHttpResponse
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from accounts.models import User
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm
from utils.check_code import create_validate_code

from accounts import forms
from main.forms import TeacherInfoForm, SupervisorForm
import main.models as main_models
from utils.search_queryset import SearchQuerySet
from utils.mixins.view import PermRequiredMixin, LoginRequiredMixin


# Create your views here.
@login_required
def upload(request, img_type, obj_type):
    if request.method == 'POST' and request.is_ajax():
        resp = {'status': 'success'}
        if img_type == 'gravatar':
            _id = request.POST.get('item_id')
            gravatar = request.FILES['gravatar']
            gravatar.name = str(_id) + '.' + gravatar.name.split('.')[-1]
            if obj_type == 'student':
                item = main_models.Student.objects.get(id=_id)
                item.img = gravatar
                item.save()
                resp['url'] = item.img.url
        return JsonResponse(resp)


def check_code(request):
    stream = io.BytesIO()
    img, code = create_validate_code()
    img.save(stream, 'png')
    request.session['CheckCode'] = code

    return StreamingHttpResponse((stream.getvalue(),))


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request, form=None):
        if not request.user.is_authenticated:
            data = {}
            if not form:
                form = forms.LoginForm()
            data['form'] = form
            data['title'] = 'Login'

            return render(request, self.template_name, data)
        else:
            msg = 'You have already logged in.'
            messages.add_message(request, messages.INFO, msg)
            referer = request.environ.get('HTTP_REFERER')
            url = referer if referer else reverse('main:home')
            return redirect(url)

    def post(self, request):
        form = forms.LoginForm(request.POST)
        check_code_val = request.session.get('CheckCode', None)
        if check_code_val and request.POST.get('checkcode').lower() == check_code_val.lower():
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']

                user = authenticate(email=email, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)

                        url = request.GET.get('next', None)
                        if not url:
                            url = reverse('main:students')
                        return redirect(url)
                    else:

                        msg = 'The user is disabled'
                        messages.add_message(request, messages.WARNING, msg)
                        return self.get(request, form)
                else:

                    msg = 'Invalid login, user does not exist'
                    messages.add_message(request, messages.ERROR, msg)
                    return self.get(request, form)

            else:
                return self.get(request, form)
        else:
            msg = 'The validate code error'
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, form)


def user_logout(request):
    logout(request)
    msg = 'Succeed to logout'
    messages.add_message(request, messages.SUCCESS, msg)
    url = reverse('accounts:login')
    return redirect(url)


class RegisterView(PermRequiredMixin, View):
    template_name = 'base_add.html'
    permission_required = 'accounts.add_user'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.RegisterForm()

        data['form'] = form
        data['add_user'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.RegisterForm(request.POST)
        if form.is_valid():

            duty = form.cleaned_data.pop('duty')
            branch = form.cleaned_data.pop('branch')
            form.cleaned_data.pop('password_confirm')

            user = User.objects.create_user(**form.cleaned_data)
            user.duty = duty
            user.branch = branch
            user.is_admin = True
            user.save()

            user.groups.add(Group.objects.get(name='User'))
            user.groups.add(Group.objects.get(name='User_' + str(user.branch)))

            msg = 'Successfully Registered'
            messages.add_message(request, messages.SUCCESS, msg)

            return self.get(request)
        else:
            return self.get(request, form)


class UsersView(PermRequiredMixin, View):
    template_name = 'accounts/users.html'
    permission_required = 'accounts.view_user'
    accept_global_perms = True

    def get(self, request, group_id=0):
        data = {}
        if group_id:
            group = Group.objects.get(pk=group_id)
            users = group.user_set.all().order_by('pk')
            data['group_id'] = int(group_id)
        else:
            users = User.objects.all().order_by('pk')
            data['all'] = True

        data['count'] = users.count()

        search_content = request.GET.get('s', '')

        users = SearchQuerySet(users, search_content).result() if search_content else users

        paginator = Paginator(users, 15)
        current_page = request.GET.get('page', 1)
        try:
            users = paginator.page(current_page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        groups = Group.objects.all()

        data['users'] = users
        data['groups'] = groups

        return render(request, self.template_name, data)


class UserView(PermRequiredMixin, View):
    template_name = 'accounts/user.html'
    permission_required = 'accounts.view_user'
    model = User
    accept_global_perms = True
    object_check = True

    def get(self, request, pk):
        data = {}

        user = self.get_object(pk)

        data['user'] = user

        groups = user.groups.all()
        data['groups'] = groups

        permissions = user.user_permissions.all()
        data['permissions'] = permissions

        return render(request, self.template_name, data)


class UserChangeView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'accounts.change_user'
    model = User
    accept_global_perms = True
    object_check = True

    def get(self, request, pk, form=None):
        data = {}
        user = self.get_object(pk)

        if not form:
            form = forms.UserForm(instance=user)
        data['form'] = form

        data['m2m_field'] = form.get_m2m_data()

        return render(request, self.template_name, data)

    def post(self, request, pk):
        user = self.get_object(pk)

        form = forms.UserForm(request.POST, instance=user)
        if form.is_valid() and request.user.is_superuser:
            user = form.save(commit=False)
            user.save()
            form.save_m2m()

            url = reverse('accounts:user', args=(pk,))
            msg = 'Succeed to update user(%s) details' % user.name
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, pk, form=form)


class GroupView(PermRequiredMixin, View):
    template_name = 'accounts/group.html'
    permission_required = 'auth.add_group'
    accept_global_perms = True
    object_check = True
    model = Group

    def get(self, request, pk):

        data = {}

        group = self.get_object(pk)

        data['group'] = group

        permissions = group.permissions.all()
        data['permissions'] = permissions

        users = group.user_set.all()
        data['users'] = users

        return render(request, self.template_name, data)


class GroupChangeView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'auth.change_group'
    accept_global_perms = True
    object_check = True
    model = Group

    def get(self, request, pk, form=None):
        data = {}
        group = self.get_object(pk)

        if not form:
            form = forms.GroupForm(instance=group)
        data['form'] = form

        data['m2m_field'] = form.get_m2m_data()

        return render(request, self.template_name, data)

    def post(self, request, pk):
        pk = int(pk)
        group = self.get_object(pk)

        form = forms.GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            url = reverse('accounts:groups')
            msg = 'Succeed to update group(%s)' % group

            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            return self.get(request, form=form, pk=pk)


class GroupAddView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'auth.add_group'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.GroupForm()
        data['form'] = form

        data['m2m_field'] = form.get_m2m_data()
        return render(request, self.template_name, data)

    def post(self, request):

        form = forms.GroupForm(request.POST)
        if form.is_valid():
            form.save()
            url = reverse('accounts:groups')
            msg = 'successfully add new group(%s)' % form.cleaned_data.get('name')

            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            return self.get(request, form=form)


class GroupsView(PermRequiredMixin, View):
    template_name = 'accounts/groups.html'
    permission_required = 'accounts.add_group'
    accept_global_perms = True

    def get(self, request):
        data = {}
        groups = Group.objects.all()
        data['title'] = ('用户组', 'User Groups')
        data['groups'] = groups
        data['add_url'] = reverse('accounts:group_add')

        return render(request, self.template_name, data)


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.ProfileForm(instance=request.user)

        data['form'] = form
        data['is_profile'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = forms.ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()

            msg = 'Succeed to update profile'
            url = reverse('accounts:profile')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class ChangePasswordView(LoginRequiredMixin, View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.ChangePasswordForm(initial={'email': request.user.email})

        data['form'] = form
        data['is_password'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = forms.ChangePasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['new_password']
            user = request.user
            user.set_password(password)

            user.save()

            msg = 'Succeed to change password'
            url = reverse('accounts:login')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherInfoView(LoginRequiredMixin, View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = TeacherInfoForm(instance=request.user.teacher_info)

        data['form'] = form
        data['m2m_field'] = form.get_m2m_data()
        data['is_teacher'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = TeacherInfoForm(data=request.POST, instance=request.user.teacher_info)
        if form.is_valid():
            form.save()

            msg = 'Succeed to update teacher info'
            url = reverse('accounts:teacher_info')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class SupervisorInfoView(LoginRequiredMixin, View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = SupervisorForm(add=False, branch=request.user.branch, instance=request.user.supervisor_info)

        data['form'] = form
        data['is_supervisor'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = SupervisorForm(data=request.POST, add=False, branch=request.user.branch,
                              instance=request.user.supervisor_info)
        if form.is_valid():
            form.save()

            msg = 'Succeed to update supervisor info'
            url = reverse('accounts:supervisor_info')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)

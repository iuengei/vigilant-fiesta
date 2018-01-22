#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from django.http import Http404, HttpResponseForbidden, JsonResponse, StreamingHttpResponse
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from accounts.auth import User
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm
from utils.check_code import create_validate_code

from . import forms
from . import models
import main.models as main_models
from utils.search_queryset import SearchQuerySet


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
                            url = reverse('main:home')
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


class RegisterView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.RegisterForm()

        data['form'] = form
        data['add_user'] = True

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
    def post(self, request):
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            duty = form.cleaned_data['duty']
            branch = form.cleaned_data['branch']

            user = User.objects.create_user(email, username, password)
            user.duty = duty
            user.branch = branch
            user.save()

            user.groups.add(Group.objects.get(name='User'))
            assign_perm('change_user', user, user)

            msg = 'Successfully Registered'
            messages.add_message(request, messages.SUCCESS, msg)

            return self.get(request)
        else:
            return self.get(request, form)


class UsersView(View):
    template_name = 'accounts/users.html'

    @method_decorator(permission_required_or_403('accounts.change_user', accept_global_perms=True))
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


class UserView(View):
    template_name = 'accounts/user.html'

    @method_decorator(permission_required_or_403('accounts.change_user', accept_global_perms=True))
    def get(self, request, pk):
        data = {}
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404
        data['user'] = user

        groups = user.groups.all()
        data['groups'] = groups

        permissions = user.user_permissions.all()
        data['permissions'] = permissions

        return render(request, self.template_name, data)


class UserChangeView(View):
    template_name = 'form_edit.html'

    @method_decorator(permission_required_or_403('main.change_user', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

        if not form:
            form = forms.UserForm(instance=user)
        data['form'] = form

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.change_user', accept_global_perms=True))
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404
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


class GroupView(View):
    template_name = 'accounts/group.html'

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
    def get(self, request, pk):
        pk = int(pk)
        data = {}
        try:
            group = Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        data['group'] = group

        permissions = group.permissions.all()
        data['permissions'] = permissions

        users = group.user_set.all()
        data['users'] = users

        return render(request, self.template_name, data)


class GroupChangeView(View):
    template_name = 'accounts/group_edit.html'

    @method_decorator(permission_required_or_403('accounts.change_user', accept_global_perms=True))
    def get(self, request, pk):
        pk = int(pk)
        data = {}
        try:
            group = Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        form = forms.GroupForm(instance=group)
        data['form'] = form

        data['m2m_field'] = {
            'name': 'permissions',
            'form': form,
            'filter_args': form.filter_fields,
            'filter_form': (getattr(form, field) for field in form.filter_fields)
        }

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.change_user', accept_global_perms=True))
    def post(self, request, pk):
        pk = int(pk)
        try:
            group = Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        form = forms.GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            url = reverse('accounts:groups')
            msg = 'Succeed to update group(%s)' % group.__str__()

            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            return self.get(request, form=form, pk=pk)


class GroupAddView(View):
    template_name = 'accounts/group_edit.html'

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
    def get(self, request):

        data = {'form': forms.GroupForm()}
        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
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


class GroupsView(View):
    template_name = 'accounts/groups.html'

    @method_decorator(permission_required_or_403('accounts.add_user', accept_global_perms=True))
    def get(self, request):
        data = {}
        groups = Group.objects.all()
        data['title'] = ('用户组', 'User Groups')
        data['groups'] = groups
        data['add_url'] = reverse('accounts:group_add')

        return render(request, self.template_name, data)


class ProfileView(View):
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


class ChangePasswordView(View):
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


class TeacherInfoView(View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.TeacherChangeForm(instance=request.user.teacher_info)

        data['form'] = form
        data['is_teacher'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = forms.TeacherChangeForm(data=request.POST, instance=request.user.teacher_info)
        if form.is_valid():
            form.save()

            msg = 'Succeed to update teacher info'
            url = reverse('accounts:teacher_info')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class SupervisorInfoView(View):
    template_name = 'accounts/user_profile.html'

    @method_decorator(login_required)
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.SupervisorForm(add=False, branch=request.user.branch, instance=request.user.supervisor_info)

        data['form'] = form
        data['is_supervisor'] = True

        return render(request, self.template_name, data)

    @method_decorator(login_required)
    def post(self, request):
        form = forms.SupervisorForm(data=request.POST, add=False, branch=request.user.branch,
                                    instance=request.user.supervisor_info)
        if form.is_valid():
            form.save()

            msg = 'Succeed to update supervisor info'
            url = reverse('accounts:supervisor_info')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherAddView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('accounts.add_teacher', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.TeacherForm()

        data['form'] = form
        data['add_teacher'] = True

        data['m2m_field'] = {
            'name': 'grades',
            'form': form,
            'filter_args': form.filter_fields,
            'filter_form': (getattr(form, field) for field in form.filter_fields)
        }

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_teacher', accept_global_perms=True))
    def post(self, request):
        form = forms.TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            teacher = form.save(commit=False)
            teacher.save()
            form.save_m2m()

            msg = 'Succeed to add a new teacher'
            url = reverse('accounts:teacher_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class SupervisorAddView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.SupervisorForm(branch=request.user.branch)

        data['form'] = form
        data['add_supervisor'] = True

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def post(self, request):
        form = forms.SupervisorForm(request.POST)
        if form.is_valid():
            supervisor = form.save(commit=False)
            supervisor.save()
            form.save_m2m()

            msg = 'Succeed to add a new supervisor'
            url = reverse('accounts:supervisor_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherChangeView(View):
    template_name = 'form_edit.html'
    form = forms.TeacherChangeForm

    @method_decorator(permission_required_or_403('accounts.change_teacher', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            teacher = models.Teacher.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        if request.user.perm_obj.has_perm('change_teacher', teacher):
            if not form:
                form = self.form(instance=teacher)

            data['form'] = form

            return render(request, self.template_name, data)
        else:
            return HttpResponseForbidden(content='你没有权限')

    @method_decorator(permission_required_or_403('accounts.change_teacher', accept_global_perms=True))
    def post(self, request, pk):
        try:
            teacher = models.Teacher.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        print(request.POST.getlist('grades'))
        if request.user.perm_obj.has_perm('main.change_teacher', teacher):

            form = self.form(request.POST, instance=teacher, add=False)
            if form.is_valid():
                teacher = form.save(commit=False)
                update_fields = form.changed_data

                if 'grades' in update_fields:
                    update_fields.remove('grades')

                teacher.save(update_fields=update_fields)
                form.save_m2m()

                url = reverse('accounts:teachers')
                msg = 'Succeed to update teacher details'
                messages.add_message(request, messages.SUCCESS, msg)
                return redirect(url)
            print(form.errors)
            return self.get(request, pk, form=form)
        else:
            return HttpResponseForbidden(content='你没有权限')


class TeachersView(View):
    template_name = 'main/obj_list_js.html'
    fields = ['name', 'sex', 'age', 'subject', 'branch', 'work_type', 'mobile']

    @method_decorator(permission_required_or_403('accounts.add_teacher', accept_global_perms=True))
    def get(self, request):
        data = {}

        branch = request.user.branch
        items = models.Teacher.objects.filter(branch=branch) if branch else models.Teacher.objects.all()

        data['items'] = items
        data['title'] = ('教师列表', 'Teacher List')
        data['fields'] = self.fields
        data['model'] = models.Teacher

        return render(request, self.template_name, data)

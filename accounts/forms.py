#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from accounts.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from utils.mixins.form import FormFieldDisabledMixin, FormM2MFieldMixin


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=256, label='邮箱')
    password = forms.CharField(max_length=256, widget=forms.PasswordInput, label='密码')


class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=256, label='邮箱')
    name = forms.CharField(max_length=256, label='姓名')
    password = forms.CharField(max_length=256, widget=forms.PasswordInput, label='密码')
    password_confirm = forms.CharField(max_length=256, widget=forms.PasswordInput, label='输入相同密码')
    duty = forms.IntegerField(initial=0, widget=forms.HiddenInput, label='职位')
    branch = forms.IntegerField(widget=forms.Select(choices=User.branch_choices), label='校区')

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError('Two passwords are not the same')


class UserForm(FormM2MFieldMixin,
               forms.ModelForm):
    m2m_filed = 'groups'

    class Meta:
        model = User
        fields = ['email', 'name', 'duty', 'branch', 'groups', 'is_admin', 'is_superuser']


class ProfileForm(FormFieldDisabledMixin,
                  forms.ModelForm):
    disabled_exclude = ['email']

    class Meta:
        model = User
        fields = ['email', 'name', 'duty', 'branch']


class ChangePasswordForm(forms.Form):
    email = forms.EmailField(max_length=256, widget=forms.HiddenInput)
    old_password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    new_password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=256, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password != confirm_password:
            raise forms.ValidationError('Two passwords are not the same')

        email = cleaned_data.get('email')
        password = cleaned_data.get('old_password')
        user = authenticate(email=email, password=password)
        if user is None:
            raise forms.ValidationError('username and password does not match')


class GroupForm(FormM2MFieldMixin,
                forms.ModelForm):

    m2m_filed = 'permissions'
    m2m_filter_args = ['content_type']

    class Meta:
        model = Group
        fields = '__all__'

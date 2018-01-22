#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from accounts.auth import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate
from accounts import models


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=256, label='邮箱')
    password = forms.CharField(max_length=256, widget=forms.PasswordInput, label='密码')


class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=256)
    username = forms.CharField(max_length=256)
    password = forms.CharField(max_length=256, widget=forms.PasswordInput)
    password_confirm = forms.CharField(max_length=256, widget=forms.PasswordInput)
    duty = forms.IntegerField(initial=0, widget=forms.HiddenInput)
    branch = forms.IntegerField(widget=forms.Select(choices=User.branch_choices))

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError('Two passwords are not the same')


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'name', 'duty', 'branch', 'groups', 'is_admin', 'is_superuser']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'name', 'duty', 'branch']

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'email':
                self.fields[field].disabled = True


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


class TeacherForm(forms.ModelForm):
    filter_fields = []

    class Meta:
        model = models.Teacher
        fields = '__all__'


class TeacherChangeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TeacherChangeForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'mobile':
                self.fields[field].disabled = True

    class Meta:
        model = models.Teacher
        fields = ['sex', 'age', 'subject', 'mobile', 'grades']


class SupervisorForm(forms.ModelForm):
    branch = forms.IntegerField(widget=forms.Select)

    def __init__(self, *args, branch=0, add=True, **kwargs):
        super(SupervisorForm, self).__init__(*args, **kwargs)
        self.fields['branch'].widget.choices = [
            models.User.branch_choices[branch]] if branch else models.User.branch_choices
        if not add:
            self.fields['id_card'].disabled = True
            self.fields.pop('name')
            self.fields.pop('branch')

    class Meta:
        model = models.Supervisor
        fields = '__all__'


class GroupForm(forms.ModelForm):
    filter_fields = []

    class Meta:
        model = Group
        fields = '__all__'

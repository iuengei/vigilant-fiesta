#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
from utils.response import BaseResponse
from django.shortcuts import redirect


def auth_login_redirect(func):

    def inner(self, *args, **kwargs):
        if self.user.is_authenticated:
            return func(self, *args, **kwargs)
        else:
            return redirect('/login', self)
    return inner


def auth_login_json(func):
    def inner(self, *args, **kwargs):
        if not self.session['is_login']:
            rep = BaseResponse()
            rep.summary = "auth failed"
            self.write(json.dumps(rep.__dict__))
            return
        func(self, *args, **kwargs)
    return inner


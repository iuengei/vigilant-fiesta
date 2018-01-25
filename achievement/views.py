from achievement import models
from achievement import forms
from django.shortcuts import render, HttpResponse, Http404, redirect
from django.db.models import ObjectDoesNotExist
from django.views.generic import View
from django.contrib import messages
from utils.mixins.view import PermQuerysetMixin, LoginRequiredMixin
import main.models


# Create your views here.


class TestsView(PermQuerysetMixin, View):
    template_name = 'obj_list_js.html'
    model = models.Test
    fields = ['name', 'exam_type', 'branch', 'create_time', 'initiator']
    permission_required = 'achievement.view_test'

    def get(self, request):
        data = self.base_dict()
        data['items'] = self.get_queryset()
        data['title'] = ('测试列表', 'Test List')

        return render(request, self.template_name, data)


class AchievementsView(PermQuerysetMixin, View):
    template_name = 'obj_list_js.html'
    fields = ['student', 'exam', 'exam_paper', 'score', 'initiator']
    permission_required = 'achievement.view_student'
    model = main.models.Student

    def get(self, request):
        data = dict()
        data['items'] = models.Achievement.objects.filter(student__in=self.get_queryset())
        data['title'] = ('成绩列表', 'Achievement List')
        data['model'] = models.Achievement
        data['fields'] = self.fields

        return render(request, self.template_name, data)


class AchievementAddView(LoginRequiredMixin, View):
    template_name = 'achievement/achievement_add.html'

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.AchievementForm(user=request.user)
        data['form'] = form
        data['model'] = models.Achievement
        data['title'] = '统一测试'
        data['is_achievement'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.AchievementForm(request.POST, user=request.user)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.initiator = request.user
            exam.save()
            form.save_m2m()
            msg = 'Succeed to add one exam.'
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(request.environ.get('HTTP_REFERER'))
        else:
            return self.get(request, form)


class TestAddView(LoginRequiredMixin, View):
    template_name = 'achievement/achievement_add.html'

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.TestForm()
        data['form'] = form
        data['model'] = models.Achievement
        data['title'] = '添加测验'
        data['is_test'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.branch = request.user.branch
            test.initiator = request.user
            test.save()
            form.save_m2m()
            msg = 'Succeed to add one test.'
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(request.environ.get('HTTP_REFERER'))
        else:
            return self.get(request, form)


class PaperAddView(LoginRequiredMixin, View):
    template_name = 'achievement/achievement_add.html'

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.PaperForm()
        data['form'] = form
        data['model'] = models.Achievement
        data['title'] = '添加试卷'
        data['is_paper'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.PaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.branch = request.user.branch
            paper.author = request.user
            paper.save()
            form.save_m2m()
            msg = 'Succeed to add one exam paper.'
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(request.environ.get('HTTP_REFERER'))
        else:
            return self.get(request, form)


class PapersView(PermQuerysetMixin, View):
    template_name = 'obj_list_js.html'
    model = models.Paper
    fields = ['name', 'subject', 'grade', 'file', 'branch', 'create_time', 'author']
    permission_required = 'achievement.view_paper'
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': True,
    }

    def get(self, request):
        data = self.base_dict()
        data['items'] = self.get_queryset()
        data['title'] = ('试卷列表', 'Paper List')

        return render(request, self.template_name, data)
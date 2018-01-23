import json
from django.shortcuts import render, HttpResponse, Http404, redirect
from django.http import Http404, HttpResponseForbidden, JsonResponse, StreamingHttpResponse
from django.db.models import ObjectDoesNotExist
from django.views.generic import View
from guardian.shortcuts import get_objects_for_user, get_users_with_perms
from django.utils.decorators import method_decorator
from guardian.decorators import permission_required_or_403
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from main import models
from accounts import models as accounts_models
from main import forms
from utils.search_queryset import SearchQuerySet
from guardian.shortcuts import assign_perm, remove_perm


# Create your views here.
class Index(View):
    template_name = 'main/home.html'

    def get(self, request):
        return render(request, self.template_name)


class StudentsView(View):
    template_name = 'main/obj_list_js.html'
    fields = ['name', 'sex', 'grade', 'branch', 'supervisor']

    def get(self, request):
        data = {}
        if request.user.is_staff:
            branch = request.user.branch
            students = models.Student.objects.filter(
                branch=branch).select_related() if branch else models.Student.objects.select_related()
        else:
            students = get_objects_for_user(request.user, ['main.change_student', 'main.view_student'],
                                            accept_global_perms=False, any_perm=True).select_related()
        data['items'] = students
        data['title'] = ('学生列表', 'Student List')
        data['fields'] = self.fields
        data['model'] = models.Student
        data['detail'] = 'name'

        return render(request, self.template_name, data)


class StudentView(View):
    template_name = 'main/student_details.html'

    @method_decorator(login_required)
    def get(self, request, pk):
        data = {}
        try:
            student = models.Student.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm(['main.change_student', 'main.view_student'], student):

            data['details'] = student
            data['title'] = ('学生详情', 'Student Details')

            tags = student.tag_set.order_by('-create_time').select_related('author')
            teachers = student.teachers.all()
            data['tags'] = tags
            data['teachers'] = teachers
            data['tag_form'] = forms.TagForm(initial={'author': request.user.id, 'to': pk})

            return render(request, self.template_name, data)
        else:
            return redirect(reverse('403'))


class TagView(View):
    @method_decorator(login_required)
    def post(self, request, to, author):
        resp = {'status': 'success'}
        form = forms.TagForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['to'] == int(to) and form.cleaned_data['author'] == int(author):
                models.Tag.objects.create(content=form.data.get('content'),
                                          author_id=form.data.get('author'),
                                          to_id=form.data.get('to'))
        else:
            resp['status'] = 'error'
            resp['error_message'] = '不得超过256个字符'

        resp = json.dumps(resp)
        return HttpResponse(resp)


class StudentChangeView(View):
    template_name = 'main/student_edit.html'

    @method_decorator(login_required)
    def get(self, request, pk, form=None):
        data = {}
        try:
            student = models.Student.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_student', student):
            if not form:
                form = forms.StudentForm(instance=student, add=False, user=request.user)

            data['form'] = form
            data['parents_formset'] = form.parents
            data['edit_detail'] = True
            data['pk'] = pk

            return render(request, self.template_name, data)
        else:
            return redirect(reverse('403'))

    @method_decorator(login_required)
    def post(self, request, pk):
        try:
            student = models.Student.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_student', student):
            form = forms.StudentForm(request.POST, instance=student, add=False, user=request.user)
            parents_formset = form.parents
            if form.is_valid() and parents_formset.is_valid():
                student = form.save(commit=False)
                student.save()
                form.save_m2m()

                parents_formset.save()

                url = reverse('main:student_edit', args=(pk,))
                msg = 'Succeed to update student details'
                messages.add_message(request, messages.SUCCESS, msg)
                return redirect(url)
            return self.get(request, pk, form=form)
        else:
            return redirect(reverse('403'))


class StudentTeacherView(View):
    template_name = 'main/student_edit.html'

    @method_decorator(login_required)
    def get(self, request, pk, form=None):
        data = {}
        try:
            student = models.Student.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_student', student):
            if not form:
                form = forms.StudentTeacherForm(instance=student)

            data['m2m_field'] = {
                'name': 'teachers',
                'form': form,
                'filter_args': form.filter_fields,
                'filter_form': (getattr(form, field) for field in form.filter_fields)
            }

            data['edit_teacher'] = True
            data['pk'] = pk

            return render(request, self.template_name, data)
        else:
            return redirect(reverse('403'))

    @method_decorator(login_required)
    def post(self, request, pk):
        try:
            student = models.Student.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_student', student):
            form = forms.StudentTeacherForm(request.POST, instance=student)
            if form.is_valid():
                student = form.save(commit=False)

                if form.has_changed():
                    elapsed = get_users_with_perms(student).filter(duty=2)
                    current = models.User.objects.filter(teacher_info__in=form.cleaned_data.get('teachers'))

                    add = current.difference(elapsed)
                    rem = elapsed.difference(current)
                    _ = [remove_perm('view_student', _, student) for _ in rem] if rem else None
                    _ = [assign_perm('view_student', _, student) for _ in add] if add else None

                student.save()
                form.save_m2m()
                url = reverse('main:student_teacher_edit', args=(pk,))
                msg = 'Succeed to update student details'
                messages.add_message(request, messages.SUCCESS, msg)
                return redirect(url)
            return self.get(request, pk, form=form)
        else:
            return redirect(reverse('403'))


class StudentAddView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('main.add_student', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.StudentForm(user=request.user)

        data['form'] = form
        data['add_student'] = True

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.add_student', accept_global_perms=True))
    def post(self, request):
        form = forms.StudentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            teacher = form.save(commit=False)
            teacher.save()
            form.save_m2m()

            msg = 'Succeed to add student'
            url = reverse('main:student_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherAddView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('main.add_teacher', accept_global_perms=True))
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

    @method_decorator(permission_required_or_403('main.add_teacher', accept_global_perms=True))
    def post(self, request):
        form = forms.TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            teacher = form.save(commit=False)
            teacher.save()
            form.save_m2m()

            msg = 'Succeed to add a new teacher'
            url = reverse('main:teacher_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class SupervisorAddView(View):
    template_name = 'base_add.html'

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.SupervisorForm(branch=request.user.branch)

        data['form'] = form
        data['add_supervisor'] = True

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
    def post(self, request):
        form = forms.SupervisorForm(request.POST)
        if form.is_valid():
            supervisor = form.save(commit=False)
            supervisor.save()
            form.save_m2m()

            msg = 'Succeed to add a new supervisor'
            url = reverse('main:supervisor_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherChangeView(View):
    template_name = 'form_edit.html'
    form = forms.TeacherChangeForm

    @method_decorator(permission_required_or_403('main.change_teacher', accept_global_perms=True))
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

    @method_decorator(permission_required_or_403('main.change_teacher', accept_global_perms=True))
    def post(self, request, pk):
        try:
            teacher = models.Teacher.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        print(request.POST.getlist('grades'))
        if request.user.perm_obj.has_perm('main.change_teacher', teacher):

            form = self.form(request.POST, instance=teacher)
            if form.is_valid():
                teacher = form.save(commit=False)
                update_fields = form.changed_data

                if 'grades' in update_fields:
                    update_fields.remove('grades')

                teacher.save(update_fields=update_fields)
                form.save_m2m()

                url = reverse('main:teachers')
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

    @method_decorator(permission_required_or_403('main.add_teacher', accept_global_perms=True))
    def get(self, request):
        data = {}

        branch = request.user.branch
        items = models.Teacher.objects.filter(branch=branch) if branch else models.Teacher.objects.all()

        data['items'] = items
        data['title'] = ('教师列表', 'Teacher List')
        data['fields'] = self.fields
        data['model'] = models.Teacher

        return render(request, self.template_name, data)

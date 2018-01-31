import json
from django.shortcuts import render, HttpResponse, redirect
from django.views.generic import View
from guardian.shortcuts import get_users_with_perms

from django.core.urlresolvers import reverse
from django.contrib import messages

from main import models
from accounts.models import Group
from main import forms
from guardian.shortcuts import assign_perm, remove_perm
from utils.mixins.view import PermQuerysetMixin, PermRequiredMixin


# Create your views here.
class Index(View):
    template_name = 'main/home.html'

    def get(self, request):
        return render(request, self.template_name)


class StudentsView(PermQuerysetMixin, View):
    template_name = 'main/obj_list_js.html'
    model = models.Student
    fields = ['name', 'sex', 'grade', 'branch', 'supervisor']
    permission_required = ['main.change_student', 'main.view_student']
    get_objects_for_user_extra_kwargs = {
        'any_perm': True,
        'accept_global_perms': False,
    }

    def get(self, request):
        data = self.base_dict()

        data['items'] = self.get_queryset().select_related()

        data['title'] = ('学生列表', 'Student List')
        data['detail'] = 'name'

        return render(request, self.template_name, data)


class StudentView(PermRequiredMixin, View):
    template_name = 'main/student_details.html'
    permission_required = 'main.change_student'
    return_403 = True
    model = models.Student
    object_check = True

    def get(self, request, pk):
        data = dict()

        student = self.get_object(pk)
        data['details'] = student
        data['title'] = ('学生详情', 'Student Details')

        tags = student.tag_set.order_by('-create_time').select_related('author')
        teachers = student.teachers.all()
        data['tags'] = tags
        data['teachers'] = teachers
        data['tag_form'] = forms.TagForm(initial={'author': request.user.id, 'to': pk})

        return render(request, self.template_name, data)


class TagView(PermRequiredMixin, View):
    permission_required = 'main.add_tag'
    accept_global_perms = True

    def post(self, request, to, author):
        resp = {'status': 'success'}

        form = forms.TagForm(request.POST)
        if form.is_valid():

            if int(form.cleaned_data['to']) == int(to) and request.user.pk == int(author):
                obj = models.Tag.objects.create(content=form.data.get('content'),
                                                author=request.user,
                                                to_id=int(to))

                assign_perm('main.change_tag', request.user, obj)
                assign_perm('main.delete_tag', request.user, obj)
            else:
                resp['status'] = 'error'
                resp['error_message'] = '2222222222符'
        else:
            resp['status'] = 'error'
            resp['error_message'] = '不得超过256个字符'

        resp = json.dumps(resp)
        return HttpResponse(resp)


class StudentChangeView(PermRequiredMixin, View):
    template_name = 'main/student_edit.html'
    permission_required = 'main.change_student'
    return_403 = True
    model = models.Student
    object_check = True

    def get(self, request, pk, form=None):
        data = {}
        student = self.get_object(pk)

        if not form:
            form = forms.StudentForm(instance=student, user=request.user)

        data['form'] = form
        data['parents_formset'] = form.parents
        data['edit_detail'] = True
        data['pk'] = pk

        return render(request, self.template_name, data)

    def post(self, request, pk):
        student = self.get_object(pk)

        form = forms.StudentForm(request.POST, instance=student, user=request.user)
        parents_formset = form.parents
        if form.is_valid() and parents_formset.is_valid():
            student = form.save(commit=False)
            student.save()
            form.save_m2m()

            parents_formset.save()

            url = request.GET.get('next', None)
            if url is None:
                url = reverse('main:student', args=(pk,))

            msg = 'Succeed to update student details'
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)
        return self.get(request, pk, form=form)


class StudentTeacherView(PermRequiredMixin, View):
    template_name = 'main/student_edit.html'
    permission_required = 'main.change_student'
    return_403 = True
    model = models.Student
    object_check = True

    def get(self, request, pk, form=None):
        data = {}

        student = self.get_object(pk)

        if not form:
            form = forms.StudentTeacherForm(instance=student, user=request.user)

        data['m2m_field'] = form.get_m2m_data()

        data['edit_teacher'] = True
        data['pk'] = pk

        return render(request, self.template_name, data)

    def post(self, request, pk):
        student = self.get_object(pk)

        form = forms.StudentTeacherForm(request.POST, instance=student, user=request.user)
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
            url = request.GET.get('next', None)
            if url is None:
                url = reverse('main:student', args=(pk,))
            msg = 'Succeed to update student details'
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, pk, form=form)


class StudentAddView(PermRequiredMixin, View):
    template_name = 'base_add.html'
    permission_required = 'main.add_student'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.StudentAddForm(user=request.user)

        data['form'] = form
        data['add_student'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.StudentAddForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            student = form.save(commit=False)
            student.save()
            form.save_m2m()

            assign_perm('change_student', student.supervisor.user_info, student)
            assign_perm('view_student', student.supervisor.user_info, student)

            user_group = Group.objects.get(name='User_'+str(student.branch))
            assign_perm('change_student', user_group, student)
            assign_perm('view_student', user_group, student)

            msg = 'Succeed to add student'
            url = reverse('main:student_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherAddView(PermRequiredMixin, View):
    template_name = 'base_add.html'
    permission_required = 'main.add_teacher'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.TeacherForm(user=request.user)

        data['form'] = form
        data['add_teacher'] = True

        data['m2m_field'] = form.get_m2m_data()

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            teacher = form.save(commit=False)
            teacher.save()
            form.save_m2m()

            assign_perm('change_teacher', Group.objects.get(name='User_' + str(teacher.branch)), teacher)
            assign_perm('view_teacher', Group.objects.get(name='User_' + str(teacher.branch)), teacher)

            msg = 'Succeed to add a new teacher'
            url = reverse('main:teacher_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class SupervisorAddView(PermRequiredMixin, View):
    template_name = 'base_add.html'
    permission_required = 'main.add_supervisor'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.SupervisorForm(branch=request.user.branch)

        data['form'] = form
        data['add_supervisor'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.SupervisorForm(request.POST)
        if form.is_valid():
            supervisor = form.save(commit=False)
            supervisor.save()
            form.save_m2m()

            assign_perm('view_supervisor', Group.objects.get(name='User_' + str(supervisor.branch)), supervisor)

            msg = 'Succeed to add a new supervisor'
            url = reverse('main:supervisor_add')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class TeacherChangeView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'main.change_teacher'
    model = models.Teacher
    object_check = True
    accept_global_perms = True

    def get(self, request, pk, form=None):
        data = {}

        teacher = self.get_object(pk)

        if not form:
            form = forms.TeacherChangeForm(instance=teacher)

        data['form'] = form
        data['m2m_field'] = form.get_m2m_data()
        data['width_col'] = (7, 2)

        return render(request, self.template_name, data)

    def post(self, request, pk):
        teacher = self.get_object(pk)

        form = forms.TeacherChangeForm(request.POST, instance=teacher)
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


class TeachersView(PermQuerysetMixin, View):
    template_name = 'main/obj_list_js.html'
    fields = ['name', 'sex', 'age', 'subject', 'branch', 'work_type', 'mobile']
    permission_required = 'main.view_teacher'
    model = models.Teacher
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': True,
    }

    def get(self, request):
        data = self.base_dict()
        data['items'] = self.get_queryset()
        data['title'] = ('教师列表', 'Teacher List')
        return render(request, self.template_name, data)


class InterviewsView(PermQuerysetMixin, View):
    template_name = 'main/interviews.html'
    fields = ['name', 'sex', 'age', 'subject', 'address', 'mobile', 'level', 'result', 'author', 'create_time']
    permission_required = 'main.view_interview'
    model = models.Interview
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': True,
    }

    def get(self, request):
        data = self.base_dict()
        data['items'] = self.get_queryset()
        data['title'] = ('教师招聘', 'Teacher Interviews')

        return render(request, self.template_name, data)


class InterviewAddView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'main.add_interview'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.InterviewForm(user=request.user)

        data['form'] = form

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.InterviewForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            interview = form.save(commit=False)
            interview.author = request.user
            interview.save()
            form.save_m2m()

            user_group = Group.objects.get(name='User_' + str(interview.branch))
            assign_perm('main.change_interview', user_group, interview)
            assign_perm('main.view_interview', user_group, interview)

            msg = 'Succeed to add interview'
            url = reverse('main:interviews')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)

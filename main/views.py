import json
from django.shortcuts import render, HttpResponse, Http404, redirect
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
            url = reverse('main:add_student')
            messages.add_message(request, messages.SUCCESS, msg)
            return redirect(url)

        return self.get(request, form)


class CoursesView(View):
    template_name = 'main/courses.html'
    fields = ['student', 'teacher', 'lesson_time', 'lesson_plan', 'attendance', 'status']

    def get(self, request):
        data = {}
        students = get_objects_for_user(request.user, 'main.change_student', accept_global_perms=True)
        plan_count = models.CoursePlan.objects.filter(student__in=students).filter(status=False).count()

        items = models.CoursesRecord.objects.filter(student__student__in=students)

        search_content = request.GET.get('s', '')
        if search_content:
            search_content = search_content.split(' ')
            items = SearchQuerySet(items, search_content).result()

        order_by = request.GET.get('o', '')
        if order_by:
            items = items.order_by(*order_by.split(':'))
        else:
            items = items.order_by('status')

        paginator = Paginator(items, 15)
        current_page = request.GET.get('page', 1)
        try:
            items = paginator.page(current_page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        data['items'] = items
        data['is_courses'] = True
        data['plan_count'] = plan_count
        data['title'] = ('排课记录', 'Courses Record')
        data['fields'] = self.fields
        data['model'] = models.CoursesRecord

        return render(request, self.template_name, data)


def get_plan_ajax(request):
    data = {}
    students = get_objects_for_user(request.user, 'main.change_student', accept_global_perms=True)
    students_dict = students.values('pk', 'branch', 'grade')
    for student in students_dict:
        branch = student['branch']
        pk = student['pk']
        grade = student['grade']
        if branch in data:
            if grade in data[branch]:
                data[branch][grade][pk] = {}
            else:
                data[branch][grade] = {}
                data[branch][grade][pk] = {}
        else:
            data[branch] = {}
            data[branch][grade] = {}
            data[branch][grade][pk] = {}
    return HttpResponse(json.dumps(data))


class CoursePlanView(View):
    template_name = 'main/course_plan.html'
    fields = ['student', 'grade', 'subject', 'plan_time', 'hours', 'status']

    def get(self, request, form=None):
        data = {}
        students = get_objects_for_user(request.user, 'main.change_student', accept_global_perms=False)
        if not form:
            form = forms.CoursePlanForm(user=request.user)
        data['form'] = form
        data['branch'] = form.branch
        items = models.CoursePlan.objects.filter(student__in=students).select_related()
        plan_count = items.filter(status=False).count()

        search_content = request.GET.get('s', '')
        if search_content:
            search_content = search_content.split(' ')
            items = SearchQuerySet(items, search_content).result()

        order_by = request.GET.get('o', '')
        items = items.order_by(*order_by.split(':')) if order_by else items.order_by('status')

        data['items'] = items
        data['plan_count'] = plan_count
        data['title'] = ('计划排课', 'Course Plan')
        data['fields'] = self.fields
        data['is_courseplan'] = True
        data['model'] = models.CoursePlan

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.add_courseplan', accept_global_perms=True))
    def post(self, request):
        form = forms.CoursePlanForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()

            url = reverse('main:course_plan')
            msg = 'Successfully add a new course plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            return self.get(request, form=form)


class CoursePlanDeleteView(View):
    @method_decorator(permission_required_or_403('main.delete_courseplan', accept_global_perms=True))
    def get(self, request):
        if request.is_ajax():
            resp = True
            print(request.POST)
            item_id = request.GET.get('item_id')
            try:
                models.CoursePlan.objects.get(id=item_id).delete()
            except:
                resp = False
            resp = json.dumps(resp)
            return HttpResponse(resp)
        else:
            return redirect(reverse('403'))


class CourseChainView(View):
    template_name = 'main/course_chain.html'

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            course_plan = models.CoursePlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if course_plan.status:
            raise Http404

        if not form:
            form = forms.CourseChainForm(course_plan=course_plan)
        data['form'] = form
        data['plan_form'] = form.course_plan

        data['title'] = ('计划排课', 'Course Plan')

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def post(self, request, pk):
        try:
            course_plan = models.CoursePlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if course_plan.status:
            raise Http404

        form = forms.CourseChainForm(request.POST, course_plan=course_plan)
        plan_form = form.course_plan
        if form.is_valid() and not plan_form.has_changed():
            obj = form.save(commit=False)
            plan = plan_form.save(commit=False)
            if obj.teacher.branch == plan.student.branch:
                obj.student = course_plan
                obj.save()
                form.save_m2m()

                plan.status = True
                plan.save()
                form.save_m2m()

                url = reverse('main:courses')
                msg = 'Successfully finish a plan.'
                messages.add_message(request, messages.SUCCESS, msg)

                return redirect(url)
            else:
                msg = 'Please choose teacher with the same branch.'
                form.add_error('teacher', msg)
        return self.get(request, pk=pk, form=form)


class CourseChangeView(View):
    template_name = 'main/course_chain.html'

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            course = models.CoursesRecord.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        course_plan = course.student

        teachers = course_plan.student.teachers

        if not form:
            form = forms.CourseChainForm(course_plan=course_plan, teachers=teachers, instance=course)
        data['form'] = form
        data['plan_form'] = form.course_plan
        data['model'] = models.CoursesRecord

        data['title'] = ('计划排课', 'Course Plan')

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('accounts.add_supervisor', accept_global_perms=True))
    def post(self, request, pk):
        try:
            course = models.CoursesRecord.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        course_plan = course.student
        teachers = course_plan.student.teachers

        form = forms.CourseChainForm(request.POST, course_plan=course_plan, teachers=teachers, instance=course)
        plan_form = form.course_plan
        if form.is_valid() and not plan_form.has_changed():
            obj = form.save(commit=False)
            plan = plan_form.save(commit=False)
            if obj.teacher.branch == plan.student.branch:
                obj.student = course_plan
                obj.save()
                form.save_m2m()

                plan.status = True
                plan.save()
                form.save_m2m()

                url = reverse('main:courses')
                msg = 'Success to edit the plan.'
                messages.add_message(request, messages.SUCCESS, msg)

                return redirect(url)
            else:
                msg = 'Please choose teacher with the same branch.'
                form.add_error('teacher', msg)
        return self.get(request, pk=pk, form=form)


class LessonPlanView(View):
    template_name = 'main/obj_list_js.html'
    fields = ['title', 'file', 'author']

    def get(self, request):
        data = {}
        items = get_objects_for_user(request.user, 'main.change_lessonplan', accept_global_perms=True)
        data['items'] = items
        data['title'] = ('教案列表', 'Lesson Plan List')
        data['fields'] = self.fields
        data['model'] = models.LessonPlan

        return render(request, self.template_name, data)


class LessonPlanAddView(View):
    template_name = 'form_edit.html'

    @method_decorator(permission_required_or_403('main.add_lessonplan', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.LessonPlanForm()

        data['title'] = '新增教案'
        data['form'] = form

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.add_lessonplan', accept_global_perms=True))
    def post(self, request):
        form = forms.LessonPlanForm(request.POST)
        print(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()

            url = reverse('main:lessonplans')
            msg = 'Successfully add a lesson plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            print(form.errors)
            return self.get(request, form=form)


class LessonPlanChangeView(View):
    template_name = 'form_edit.html'

    @method_decorator(permission_required_or_403('main.add_lessonplan', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            lesson_plan = models.LessonPlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_lessonplan', lesson_plan):
            if not form:
                form = forms.LessonPlanForm(instance=lesson_plan)

            data['title'] = '教案修改'
            data['form'] = form

            return render(request, self.template_name, data)
        else:
            return redirect(reverse('403'))

    @method_decorator(permission_required_or_403('main.add_lessonplan', accept_global_perms=True))
    def post(self, request, pk):
        try:
            lesson_plan = models.LessonPlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('main.change_lessonplan', lesson_plan):
            form = forms.LessonPlanForm(request.POST, instance=lesson_plan)

            if form.is_valid():
                form.save()

                url = reverse('main:lessonplans')
                msg = 'Successfully edit a lesson plan.'
                messages.add_message(request, messages.SUCCESS, msg)

                return redirect(url)
            else:
                print(form.errors)
                return self.get(request, form=form)
        else:
            return redirect(reverse('403'))





def test1(request):

    print(request.user.perm_obj)
    print(id(request.user.perm_obj))
    print(request.user.perm_obj.core)
    print(id(request.user.perm_obj.core))
    return HttpResponse('test')
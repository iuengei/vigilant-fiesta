import json
from django.shortcuts import render, HttpResponse, Http404, redirect
from django.db.models import ObjectDoesNotExist
from django.views.generic import View
from guardian.shortcuts import get_objects_for_user
from django.utils.decorators import method_decorator
from guardian.decorators import permission_required_or_403
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from course import models
from course import forms
from utils.search_queryset import SearchQuerySet
from utils.mixins.view import PermQuerysetMixin, PermRequiredMixin
from guardian.shortcuts import assign_perm, remove_perm
from accounts.models import Group


# Create your views here.


class CoursesView(PermQuerysetMixin, View):
    template_name = 'course/courses.html'
    fields = ['student', 'teacher', 'lesson_time', 'lesson_plan', 'attendance', 'status']
    model = models.CoursesRecord
    permission_required = 'course.view_coursesrecord'
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': False,
    }

    def get(self, request):

        students = get_objects_for_user(request.user, 'main.view_student', accept_global_perms=True)
        plan_count = models.CoursePlan.objects.filter(student__in=students).filter(status=False).count()

        items = self.get_queryset().select_related()

        search_content = request.GET.get('s', '')
        if search_content:
            search_content = search_content.split(' ')
            items = SearchQuerySet(items, search_content).result()

        order_by = request.GET.get('o', '')
        items = items.order_by(*order_by.split(':')) if order_by else items.order_by('status')

        paginator = Paginator(items, 15)
        current_page = request.GET.get('page', 1)
        try:
            items = paginator.page(current_page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        data = self.base_dict()
        data['items'] = items
        data['is_courses'] = True
        data['plan_count'] = plan_count
        data['per_number'] = (items.number-1)*items.paginator.per_page
        data['title'] = ('排课记录', 'Courses Record')

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


class CoursePlanView(PermQuerysetMixin, View):
    template_name = 'course/course_plan.html'
    fields = ['student', 'grade', 'subject', 'plan_time', 'hours', 'status']
    model = models.CoursePlan
    permission_required = 'course.view_courseplan'
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': False,
    }

    def get(self, request, form=None):
        data = self.base_dict()
        if not form:
            form = forms.CoursePlanForm(user=request.user)
        data['form'] = form
        data['branch'] = form.branch

        items = self.get_queryset().select_related()
        plan_count = items.filter(status=False).count()

        search_content = request.GET.get('s', '')
        if search_content:
            search_content = search_content.split(' ')
            items = SearchQuerySet(items, search_content).result()

        order_by = request.GET.get('o', '')
        items = items.order_by(*order_by.split(':')) if order_by else items.order_by('status')

        paginator = Paginator(items, 15)
        current_page = request.GET.get('page', 1)
        try:
            items = paginator.page(current_page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            items = paginator.page(paginator.num_pages)

        data['items'] = items
        data['plan_count'] = plan_count
        data['per_number'] = (items.number-1)*items.paginator.per_page
        data['title'] = ('计划排课', 'Course Plan')
        data['is_courseplan'] = True

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.CoursePlanForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.save()
            form.save_m2m()

            request.user.add_obj_perm('view_courseplan', plan)
            request.user.add_obj_perm('delete_courseplan', plan)
            assign_perm('change_courseplan', Group.objects.get(name='User_' + str(plan.student.branch)), plan)

            url = reverse('course:plan')
            msg = 'Successfully add a new course plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            return self.get(request, form=form)


class CoursePlanDeleteView(View):
    @method_decorator(permission_required_or_403('course.delete_courseplan', accept_global_perms=True))
    def get(self, request):
        if request.is_ajax():
            resp = True
            print(request.POST)
            item_id = request.GET.get('item_id')
            try:
                models.CoursePlan.objects.get(id=item_id).delete()
            except Exception:
                resp = False
            resp = json.dumps(resp)
            return HttpResponse(resp)
        else:
            return redirect(reverse('403'))


class CourseChainView(PermRequiredMixin, View):
    template_name = 'course/course_chain.html'
    permission_required = 'course.change_courseplan'
    accept_global_perms = True
    object_check = True
    model = models.CoursePlan

    def get(self, request, pk, form=None):
        data = {}
        course_plan = self.get_object(pk)
        if course_plan.status:
            raise Http404

        if not form:
            form = forms.CourseChainForm(course_plan=course_plan)
        data['form'] = form
        data['plan_form'] = form.course_plan

        data['title'] = ('计划排课', 'Course Plan')

        return render(request, self.template_name, data)

    def post(self, request, pk):
        course_plan = self.get_object(pk)
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

                assign_perm('course.view_coursesrecord', Group.objects.get(name='User_'+str(request.user.branch)), obj)
                assign_perm('course.change_coursesrecord', Group.objects.get(name='User_'+str(request.user.branch)), obj)
                assign_perm('course.delete_coursesrecord', Group.objects.get(name='User_'+str(request.user.branch)), obj)

                assign_perm('course.view_coursesrecord', obj.teacher.user_info, obj)
                assign_perm('course.view_coursesrecord', plan.student.supervisor.user_info, obj)

                plan.status = True
                plan.save()
                form.save_m2m()

                url = reverse('course:list')
                msg = 'Successfully finish a plan.'
                messages.add_message(request, messages.SUCCESS, msg)

                return redirect(url)
            else:
                msg = 'Please choose teacher with the same branch.'
                form.add_error('teacher', msg)
        return self.get(request, pk=pk, form=form)


class CourseChangeView(PermRequiredMixin, View):
    template_name = 'course/course_chain.html'
    permission_required = 'course.change_coursesrecord'
    accept_global_perms = True
    object_check = True
    model = models.CoursesRecord

    def get(self, request, pk, form=None):
        data = {}

        course = self.get_object(pk)

        course_plan = course.student

        if not form:
            form = forms.CourseChainForm(course_plan=course_plan, instance=course)
        data['form'] = form
        data['plan_form'] = form.course_plan
        data['model'] = models.CoursesRecord

        data['title'] = ('计划排课', 'Course Plan')

        return render(request, self.template_name, data)

    def post(self, request, pk):
        course = self.get_object(pk)
        course_plan = course.student

        form = forms.CourseChainForm(request.POST, course_plan=course_plan, instance=course)

        if form.is_valid():
            obj = form.save(commit=False)
            if obj.teacher.branch == course_plan.student.branch:

                if form.has_changed() and 'teacher' in form.changed_data:
                    elapsed = course.teacher.user_info
                    current = form.cleaned_data.get('teacher').user_info

                    remove_perm('course.view_coursesrecord', elapsed, obj)
                    assign_perm('course.view_coursesrecord', current, obj)

                obj.save()
                form.save_m2m()

                url = reverse('course:list')
                msg = 'Success to edit the plan.'
                messages.add_message(request, messages.SUCCESS, msg)

                return redirect(url)
            else:
                msg = 'Please choose teacher with the same branch.'
                form.add_error('teacher', msg)
        return self.get(request, pk=pk, form=form)


class LessonPlanView(PermQuerysetMixin, View):
    template_name = 'main/obj_list_js.html'
    fields = ['title', 'file', 'author']
    permission_required = 'course.view_lessonplan'
    model = models.LessonPlan
    get_objects_for_user_extra_kwargs = {
        'accept_global_perms': True,
    }

    def get(self, request):
        data = self.base_dict()
        items = self.get_queryset()
        data['items'] = items
        data['title'] = ('教案列表', 'Lesson Plan List')

        return render(request, self.template_name, data)


class LessonPlanAddView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'course.add_lessonplan'
    accept_global_perms = True

    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.LessonPlanForm()

        data['title'] = '新增教案'
        data['form'] = form

        return render(request, self.template_name, data)

    def post(self, request):
        form = forms.LessonPlanForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()

            for u in [request.user, Group.objects.get(name='User_'+str(request.user.branch))]:
                assign_perm('course.view_lessonplan', u, obj)
                assign_perm('course.change_lessonplan', u, obj)
                assign_perm('course.delete_lessonplan', u, obj)

            url = reverse('course:lessonplans')
            msg = 'Successfully add a lesson plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            print(form.errors)
            return self.get(request, form=form)


class LessonPlanChangeView(PermRequiredMixin, View):
    template_name = 'form_edit.html'
    permission_required = 'course.change_lessonplan'
    object_check = True
    model = models.LessonPlan

    def get(self, request, pk, form=None):
        data = {}
        lesson_plan = self.get_object(pk)

        if not form:
            form = forms.LessonPlanForm(instance=lesson_plan)

        data['title'] = '教案修改'
        data['form'] = form

        return render(request, self.template_name, data)

    def post(self, request, pk):
        lesson_plan = self.get_object(pk)

        form = forms.LessonPlanForm(request.POST, instance=lesson_plan)
        if form.is_valid():
            form.save()

            url = reverse('course:lessonplans')
            msg = 'Successfully edit a lesson plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            print(form.errors)
            return self.get(request, form=form)


def test1(request):
    import random
    from main import models as main_models
    def id_card():
        id_card = '410323' + str(random.choice(range(1980, 1993))) + str(random.choice(range(1, 13))).rjust(2, '0') + \
                  str(random.choice(range(1, 31))).rjust(2, '0') + str(random.choice(range(1, 100))).rjust(3, '0') + \
                  random.choice('0123456789X')
        return id_card

    for i in range(1, 71):
        _dict = {'name': '班主任' + str(i),
                 'sex': random.choice([1, 0]),
                 'branch': random.choice(range(1, 9)),
                 'age': random.choice(range(20, 30)),
                 'id_card': id_card(),
                 'mobile': random.choice(range(13213102645, 19999999999))}
        try:
            main_models.Supervisor.objects.create(**_dict)
        except Exception as e:
            print(e)
            _id_card = id_card()
            _dict.update({'id_card': _id_card})
            try:
                main_models.Supervisor.objects.create(**_dict)
            except:
                continue

    supervisor_dict = {}

    for i in range(1, 551):
        _dict = {'name': '学生' + str(i),
                 'sex': random.choice(range(0, 2)),
                 'branch': random.choice(range(1, 9)),
                 'grade': random.choice(range(1, 13)),
                 'id_card': id_card()}
        branch = _dict.get('branch')
        if branch in supervisor_dict:
            _dict['supervisor_id'] = random.choice(supervisor_dict[branch])
        else:
            supervisor_dict[branch] = main_models.Supervisor.objects.filter(branch=branch).values_list('id',
                                                                                                       flat=True)
            _dict['supervisor_id'] = random.choice(supervisor_dict[branch])
        try:
            main_models.Student.objects.create(**_dict)
        except Exception as e:
            print(e)
            continue

    for i in range(1, 801):
        _dict = {'name': '教师' + str(i),
                 'sex': random.choice([1, 0]),
                 'branch': random.choice(range(1, 9)),
                 'age': random.choice(range(20, 51)),
                 'work_type': random.choice([1, 0]),
                 'id_card': id_card(),
                 'subject': random.choice(range(1, 10)),
                 'mobile': random.choice(range(13213102645, 19999999999))}
        try:
            main_models.Teacher.objects.create(**_dict)
        except Exception as e:
            print(e)
            _id_card = id_card()
            _dict.update({'id_card': _id_card})
            try:
                main_models.Teacher.objects.create(**_dict)
            except:
                continue

    teacher_count = main_models.Teacher.objects.count()
    for i in range(1, teacher_count + 1):
        try:
            main_models.Teacher.objects.get(id=i).grades.add(random.choice(random.choices(list(range(1, 13)), k=5)))
        except:
            continue
    return HttpResponse('test')

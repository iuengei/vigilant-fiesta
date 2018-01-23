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


# Create your views here.


class CoursesView(View):
    template_name = 'course/courses.html'
    fields = ['student', 'teacher', 'lesson_time', 'lesson_plan', 'attendance', 'status']

    def get(self, request):
        data = {}
        students = get_objects_for_user(request.user, 'main.view_student', accept_global_perms=True)
        plan_count = models.CoursePlan.objects.filter(student__in=students).filter(status=False).count()

        items = models.CoursesRecord.objects.filter(student__student__in=students).select_related()

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
        data['is_courses'] = True
        data['plan_count'] = plan_count
        data['per_number'] = (items.number-1)*items.paginator.per_page
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
    template_name = 'course/course_plan.html'
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
        data['fields'] = self.fields
        data['is_courseplan'] = True
        data['model'] = models.CoursePlan

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('course.add_courseplan', accept_global_perms=True))
    def post(self, request):
        form = forms.CoursePlanForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()

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


class CourseChainView(View):
    template_name = 'course/course_chain.html'

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
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

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
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
                # obj.plan_timedelta
                obj.save()
                form.save_m2m()

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


class CourseChangeView(View):
    template_name = 'course/course_chain.html'

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            course = models.CoursesRecord.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        course_plan = course.student

        teachers = course_plan.student.teachers

        if not form:
            form = forms.CourseChainForm(course_plan=course_plan, instance=course)
        data['form'] = form
        data['plan_form'] = form.course_plan
        data['model'] = models.CoursesRecord

        data['title'] = ('计划排课', 'Course Plan')

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('main.add_supervisor', accept_global_perms=True))
    def post(self, request, pk):
        try:
            course = models.CoursesRecord.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

        course_plan = course.student
        teachers = course_plan.student.teachers

        form = forms.CourseChainForm(request.POST, course_plan=course_plan, instance=course)
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

                url = reverse('course:list')
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
        items = get_objects_for_user(request.user, 'course.change_lessonplan', accept_global_perms=True)
        data['items'] = items
        data['title'] = ('教案列表', 'Lesson Plan List')
        data['fields'] = self.fields
        data['model'] = models.LessonPlan

        return render(request, self.template_name, data)


class LessonPlanAddView(View):
    template_name = 'form_edit.html'

    @method_decorator(permission_required_or_403('course.add_lessonplan', accept_global_perms=True))
    def get(self, request, form=None):
        data = {}
        if not form:
            form = forms.LessonPlanForm()

        data['title'] = '新增教案'
        data['form'] = form

        return render(request, self.template_name, data)

    @method_decorator(permission_required_or_403('course.add_lessonplan', accept_global_perms=True))
    def post(self, request):
        form = forms.LessonPlanForm(request.POST)
        print(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.author = request.user
            obj.save()

            url = reverse('course:lessonplans')
            msg = 'Successfully add a lesson plan.'
            messages.add_message(request, messages.SUCCESS, msg)

            return redirect(url)
        else:
            print(form.errors)
            return self.get(request, form=form)


class LessonPlanChangeView(View):
    template_name = 'form_edit.html'

    @method_decorator(permission_required_or_403('course.add_lessonplan', accept_global_perms=True))
    def get(self, request, pk, form=None):
        data = {}
        try:
            lesson_plan = models.LessonPlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('course.change_lessonplan', lesson_plan):
            if not form:
                form = forms.LessonPlanForm(instance=lesson_plan)

            data['title'] = '教案修改'
            data['form'] = form

            return render(request, self.template_name, data)
        else:
            return redirect(reverse('403'))

    @method_decorator(permission_required_or_403('course.add_lessonplan', accept_global_perms=True))
    def post(self, request, pk):
        try:
            lesson_plan = models.LessonPlan.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        if request.user.perm_obj.has_perm('course.change_lessonplan', lesson_plan):
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
        else:
            return redirect(reverse('403'))


def test1(request):
    from django.utils.datetime_safe import datetime
    default = datetime.now().minute
    print(default)
    return HttpResponse('test')

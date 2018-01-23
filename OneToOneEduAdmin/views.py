from django.apps import apps
from collections import OrderedDict
from django.db.models import ObjectDoesNotExist
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel, OneToOneRel
from django.shortcuts import render, Http404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator


def render_403(request):
    return render(request, '403.html')


class DeleteView(View):
    template_name = 'obj_delete.html'

    @method_decorator(user_passes_test(test_func=lambda u: u.is_superuser, login_url='/403.html'))
    def get(self, request, app_label, model_name, pk):
        data = {}
        model = apps.get_model(app_label=app_label, model_name=model_name)
        try:
            obj = model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        message, summary = recursive_related(obj)
        data['message'] = message
        data['summary'] = summary
        return render(request, self.template_name, data)

    @method_decorator(user_passes_test(test_func=lambda u: u.is_superuser, login_url='/403.html'))
    def post(self, request, app_label, model_name, pk):
        model = apps.get_model(app_label=app_label, model_name=model_name)
        try:
            obj = model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404
        result = request.POST.get('post')
        if result == 'yes':
            obj.delete()
            return redirect(request.POST.get('referer'))


class MessageTree(object):
    def __init__(self, obj, message=''):
        self.children = []
        self.m2m_children = []
        self.message = message
        self.obj = obj
        self.table = self.obj._meta.verbose_name


def recursive_related(obj):
    message = MessageTree(obj, message=obj._meta.verbose_name + ": " + obj.__str__())
    summary = OrderedDict()
    obj_queue = [message]
    while obj_queue:
        # 取出队列最前一位对象
        current = obj_queue.pop(0)
        if current.table in summary:
            summary[current.table] += 1
        else:
            summary[current.table] = 1

        # 获取当前对象的字段列表
        obj_fields = current.obj._meta.get_fields()
        for each in obj_fields:

            # 判断字段是否需要相关查询 m2m/m21/121
            if isinstance(each, ManyToOneRel):
                if isinstance(each, OneToOneRel):
                    if hasattr(current.obj, each.name):
                        _obj = getattr(current.obj, each.name)
                        table_name = _obj._meta.verbose_name
                        new_message = MessageTree(_obj, message=table_name + ": " + _obj.__str__())
                        current.children.append(new_message)
                        obj_queue.extend(current.children)
                else:
                    # 若关联对象不为空获取之
                    if hasattr(current.obj, each.name):
                        for i in getattr(current.obj, each.name).get_queryset():
                            table_name = i._meta.verbose_name
                            new_message = MessageTree(i, message=table_name + ": " + i.__str__())
                            current.children.append(new_message)

                        obj_queue.extend(current.children)
            elif isinstance(each, ManyToManyField) or isinstance(each, ManyToManyRel):
                # 获取关联对象,不进队列
                if hasattr(current.obj, each.name):
                    filter_dict = {current.obj._meta.model_name + '_id': current.obj.id}
                    for i in getattr(current.obj, each.name).through.objects.filter(**filter_dict):
                        table_name = i._meta.verbose_name
                        new_message = MessageTree(i, message=table_name + ": " + i.__str__())
                        current.m2m_children.append(new_message)

                        if new_message.table in summary:
                            summary[new_message.table] += 1
                        else:
                            summary[new_message.table] = 1

    return message, summary

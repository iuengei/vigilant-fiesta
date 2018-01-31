from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin, PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_content_type, get_perms_for_model, get_objects_for_group
from guardian.models import UserObjectPermission, GroupObjectPermission
from django.apps import apps
from collections import defaultdict
from accounts.models import User


class PermRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """object_check为True时需要提供model
    检查针对指定对象的权限时，从kwargs获取pk
    default:pk 或者提供object_pk指定 """
    model = None
    object_check = False

    def get_object(self, pk=None):
        if self.object_check:
            if self.model is None:
                raise AttributeError('Attribute model need be defined, instead of None.')
            pk = pk if pk else hasattr(self, 'object_pk') and self.kwargs.get(self.object_pk) or self.kwargs.get('pk',
                                                                                                                 None)
            if pk is None:
                raise KeyError('missing parameter pk.')
            return self.model.objects.get(pk=pk)
        else:
            return None


class PermQuerysetMixin(LoginRequiredMixin, PermissionListMixin):
    """model指定queryset的作用模块
    get_queryset方法返回拥有model指定权限的所有obj
    其它见PermissionListMixin"""
    model = None
    fields = '__all__'

    def base_dict(self):
        _dict = {'model': self.model,
                 'fields': self.fields}
        return _dict

    def get_queryset(self, queryset=None):
        if queryset is not None:
            if self.model and queryset.model is self.model:
                get_get_objects_for_user_kwargs = self.get_get_objects_for_user_kwargs(queryset)
            else:
                raise AttributeError("Attribute model is different of queryset's model.")
        else:
            if self.model is None:
                raise AttributeError('Attribute model need be defined, instead of None.')
            queryset = self.model.objects.all()
            get_get_objects_for_user_kwargs = self.get_get_objects_for_user_kwargs(queryset)

        return get_objects_for_user(**get_get_objects_for_user_kwargs)


class ObjectsPermsMixin(object):
    """获取用户或用户组对象权限的信息
    对象权限 default: view change delete
    add 权限则由 global perm 管理
    filter_models 为需要查看显示的model模块
    obj_model 权限对象的model模块，可以由url传入app_label和model_name动态指定，或者提供object_model属性指定
    get_objects_with_perms方法返回一个dict，包含拥有obj_model任意权限的所有obj对象，单个obj对象为键，值为所拥有此obj对象权限的list.
    """
    codenames = ['view', 'change', 'delete']
    filter_models = ['main.student', 'course.courseplan', 'course.coursesrecord']

    def base_dict(self):
        _dict = dict()
        _dict['app_label'] = self.obj_model._meta.app_label
        _dict['model_name'] = self.obj_model._meta.model_name
        _dict['model'] = self.obj_model
        _dict['codenames'] = self.obj_perms
        _dict['filter_models'] = self._get_filter_models()
        return _dict

    @property
    def obj_model(self):
        object_model = getattr(self, 'object_model', None)
        if object_model and self.obj_app_label and self.obj_model_name:
            if object_model._meta.app_label == self.obj_app_label and object_model._meta.model_name == self.obj_model_name:
                return object_model
            else:
                AttributeError('Attribute object_model has different app_label.model_name.')
        elif object_model:
            return object_model
        else:
            return apps.get_model(app_label=self.obj_app_label, model_name=self.obj_model_name)

    @property
    def obj_ctype(self):
        return get_content_type(self.obj_model)

    @property
    def obj_perms(self):
        _perms = [codename + '_' + self.obj_model._meta.model_name for codename in self.codenames]
        # return get_perms_for_model(self.obj_model).values_list('codename', flat=True)
        return _perms

    def _get_filter_models(self):
        _dict = dict()
        for _ in self.filter_models:
            app_label, model_name = _.split('.')
            _dict[model_name] = (app_label, model_name)
        return _dict

    def _get_objects_for_user(self, user, accept_global_perms):
        return get_objects_for_user(user,
                                    any_perm=True,
                                    perms=self.obj_perms,
                                    klass=self.obj_model,
                                    accept_global_perms=accept_global_perms)

    def _get_objects_for_group(self, group, accept_global_perms):
        return get_objects_for_group(group,
                                     any_perm=True,
                                     perms=self.obj_perms,
                                     klass=self.obj_model,
                                     accept_global_perms=accept_global_perms)

    def get_objects_with_perms(self, user_or_group, accept_global_perms=False):
        if isinstance(user_or_group, User):
            objs = self._get_objects_for_user(user_or_group, accept_global_perms)
            _model = UserObjectPermission
        else:
            objs = self._get_objects_for_group(user_or_group, accept_global_perms)
            _model = GroupObjectPermission

        objs_perms = _model.objects.filter(content_type=self.obj_ctype,
                                           object_pk__in=objs
                                           ).values('object_pk', 'permission__codename')

        perms_by_obj = defaultdict(list)
        for item in objs_perms:
            perms_by_obj[int(item['object_pk'])].append(item['permission__codename'])

        for obj in objs:
            perms_by_obj[obj] = perms_by_obj.pop(obj.pk)

        return dict(perms_by_obj)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.obj_app_label = self.kwargs.get('app_label', None)
        self.obj_model_name = self.kwargs.get('model_name', None)
        return super(ObjectsPermsMixin, self).dispatch(request, *args,
                                                       **kwargs)

from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin, PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_content_type, get_perms_for_model, get_objects_for_group
from guardian.models import UserObjectPermission, GroupObjectPermission
from django.apps import apps
from collections import defaultdict
from accounts.models import User


class PermRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model = None
    object_check = False

    def get_object(self, pk=None):
        if self.object_check:
            if self.model is None:
                raise AttributeError('Attribute model need be defined, instead of None.')
            pk = pk if pk else self.kwargs.get('pk', None)
            if pk is None:
                raise KeyError('missing parameter pk.')
            return self.model.objects.get(pk=pk)
        else:
            return None


class PermQuerysetMixin(LoginRequiredMixin, PermissionListMixin):
    model = None
    fields = '__all__'

    def base_dict(self):
        _dict = {'model': self.model,
                 'fields': self.fields}
        return _dict

    def get_queryset(self, queryset=None):
        if queryset is not None:
            get_get_objects_for_user_kwargs = self.get_get_objects_for_user_kwargs(queryset)
        else:
            if self.model is None:
                raise AttributeError('Attribute model need be defined, instead of None.')
            queryset = self.model.objects.all()
            get_get_objects_for_user_kwargs = self.get_get_objects_for_user_kwargs(queryset)

        return get_objects_for_user(**get_get_objects_for_user_kwargs)


class ObjectsPermsMixin(object):
    codenames = ['view', 'change', 'delete']
    filter_models = {
        'student': ('main', 'student'),
        'courseplan': ('course', 'courseplan'),
        'coursesrecord': ('course', 'coursesrecord')
    }

    def base_dict(self):
        _dict = dict()
        _dict['app_label'] = self.app_label
        _dict['model_name'] = self.model_name
        _dict['model'] = self.model
        _dict['codenames'] = [codename + '_' + self.model_name for codename in self.codenames]
        _dict['filter_models'] = self.filter_models
        return _dict

    @property
    def model(self):
        return apps.get_model(app_label=self.app_label, model_name=self.model_name)

    @property
    def ctype(self):
        return get_content_type(self.model)

    @property
    def perms(self):
        return get_perms_for_model(self.model).values_list('codename', flat=True)

    def _get_objects_for_user(self, user):
        return get_objects_for_user(user,
                                    any_perm=True,
                                    perms=self.perms,
                                    klass=self.model,
                                    accept_global_perms=False)

    def _get_objects_for_group(self, group):
        return get_objects_for_group(group,
                                     any_perm=True,
                                     perms=self.perms,
                                     klass=self.model,
                                     accept_global_perms=False)

    def get_objects_with_perms(self, user_or_group):
        if isinstance(user_or_group, User):
            objs = self._get_objects_for_user(user_or_group)
            _model = UserObjectPermission
        else:
            objs = self._get_objects_for_group(user_or_group)
            _model = GroupObjectPermission

        objs_perms = _model.objects.filter(content_type=self.ctype,
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
        self.app_label = kwargs.get('app_label', None)
        self.model_name = kwargs.get('model_name', None)
        return super(ObjectsPermsMixin, self).dispatch(request, *args,
                                                       **kwargs)

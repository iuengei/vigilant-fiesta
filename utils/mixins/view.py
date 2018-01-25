from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin, PermissionListMixin
from guardian.shortcuts import get_objects_for_user


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
            get_get_objects_for_user_kwargs = super(PermQuerysetMixin, self).get_get_objects_for_user_kwargs(queryset)
        else:
            if self.model is None:
                raise AttributeError('Attribute model need be defined, instead of None.')
            queryset = self.model.objects.all()
            get_get_objects_for_user_kwargs = super(PermQuerysetMixin, self).get_get_objects_for_user_kwargs(queryset)

        return get_objects_for_user(**get_get_objects_for_user_kwargs)

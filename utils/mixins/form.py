from collections import Iterable
from django.forms.models import fields_for_model
from django.forms import ModelChoiceField


class FormFieldQuerysetFilterMixin(object):
    """根据用户权限修改外键字段queryset值
       需要外键Model提供perm_queryset方法"""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is None:
            raise KeyError('missing parameter user.')
        for field, formfield in self.fields.items():
            if hasattr(formfield, 'queryset'):
                _model = formfield.queryset.model
                if hasattr(_model, 'perm_queryset'):
                    _queryset = formfield.queryset
                    formfield.queryset = _model.perm_queryset(_queryset, user)
                else:
                    raise NotImplementedError('Model %s missing method perm_queryset.' % _model)


class FormFieldDisabledMixin(object):
    disabled_fields = '__all__'
    disabled_exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.disabled_fields == '__all__':
            self.disabled_fields = self.fields.keys()

        if self.disabled_fields and not isinstance(self.disabled_fields, Iterable):
            raise AttributeError('Attribute disabled_fields should be iterable.')

        if self.disabled_exclude and not isinstance(self.disabled_exclude, Iterable):
            raise AttributeError('Attribute disabled_exclude should be iterable.')

        for field in self.fields:
            if field in self.disabled_fields and field not in self.disabled_exclude:
                self.fields[field].disabled = True


class FormM2MFieldMixin(object):
    m2m_filed = None
    m2m_filter_args = []
    m2m_filter_initial = {}  # filter字段对应实例的字段 eg: {'grades': 'grade'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.m2m_filed is None:
            raise AttributeError('missing m2m_field.')

    def get_m2m_data(self):
        _dict = dict()
        _dict['name'] = self.m2m_filed
        _dict['form'] = self
        _dict['filter_args'] = self.m2m_filter_args
        _dict['filter_form'] = self._get_filter_form()

        return _dict

    def _get_filter_form(self):
        _model = getattr(self._meta.model, self.m2m_filed).rel.to

        if not all(hasattr(_model, field) for field in self.m2m_filter_args):
            raise KeyError('Model %s should have all filter_args.' % _model)

        field_classes = {name: ModelChoiceField for name in self.m2m_filter_args}
        fields_dict = fields_for_model(_model, fields=self.m2m_filter_args, field_classes=field_classes)

        if self.m2m_filter_initial:
            _instance = self.instance
            for field, v in self.m2m_filter_initial.items():
                initial_value = getattr(_instance, v)
                if initial_value is None:
                    raise KeyError("The instance's attr %s should not be None." % v)

                fields_dict[field].initial = initial_value

        return (formfield.get_bound_field(self, field) for field, formfield in fields_dict.items())


class FormChainMixin(object):
    other_forms = {}

    def __init__(self, *args, **kwargs):
        instance_dict = {name: kwargs.pop(name, None) for name in self.other_forms}
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        data = args[0] if args else None
        for name, form in self.other_forms.items():
            _instance = instance_dict[name]
            if _instance is None:
                _instance = instance
            other_form = form(data, instance=_instance, prefix=name)
            setattr(self, name, other_form)

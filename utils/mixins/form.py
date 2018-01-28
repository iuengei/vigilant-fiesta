import django

from collections import Iterable
from django.forms.models import fields_for_model


class FormLimitChoicesMixin(object):
    """根据用户权限限制选择，需要传入user参数
       需要关联Model类提供perm_queryset方法
       普通字段在表单Model类或者表单类实现perm_<字段名>方法"""

    fields_filter = '__all__'

    def __init__(self, *args, user=None, **kwargs):
        if user is None:
            raise KeyError('missing parameter user.')

        super().__init__(*args, **kwargs)

        if self.fields_filter == '__all__':
            self.fields_filter = [field for field, formfield in self.fields.items() if
                                  hasattr(formfield, 'queryset') or hasattr(formfield.widget, 'choices')]

        for field in self.fields_filter:
            formfield = self.fields.get(field, None)
            if formfield is None:
                raise KeyError('FormFieldQuerysetFilterMixin has unexpected field %s.' % field)

            if hasattr(formfield, 'queryset'):
                _model = formfield.queryset.model
                if hasattr(_model, 'perm_queryset'):
                    _queryset = formfield.queryset
                    formfield.queryset = _model.perm_queryset(_queryset, user=user)
                else:
                    raise NotImplementedError('Model %s missing method perm_queryset.' % _model)

            else:

                _model = self._meta.model
                _func_name = 'perm_' + field
                _func = getattr(_model, _func_name, None) or getattr(self, _func_name, None)
                if _func is None:
                    raise NotImplementedError('The method %s is not implemented.' % _func_name)
                _choices = formfield.widget.choices
                formfield.widget.choices = _func(_choices, user)

    @staticmethod
    def perm_branch(_choices, user):
        if user.branch:
            _choices = [_tuple for _tuple in _choices if _tuple[0] == user.branch]
        return _choices

    @staticmethod
    def perm_sex(*args):
        return args[0]

    @staticmethod
    def perm_work_type(*args):
        return args[0]

    @staticmethod
    def perm_subject(*args):
        return args[0]

    @staticmethod
    def perm_grade(*args):
        return args[0]

    @staticmethod
    def perm_hours(*args):
        return args[0]


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
        _dict['m2m_error'] = self.errors.get(self.m2m_filed, None)
        _dict['filter_args'] = self.m2m_filter_args
        _dict['filter_form'] = self._get_filter_form() if self.m2m_filter_args else None
        _dict['is_disabled'] = self.is_disabled()

        return _dict

    def _get_filter_form(self):
        _mro = self.__class__.__mro__
        if django.forms.ModelForm in _mro:
            _model = getattr(self._meta.model, self.m2m_filed).rel.to

            if not all(hasattr(_model, field) for field in self.m2m_filter_args):
                raise KeyError('Model %s should have all fields of filter_args.' % _model)

            field_classes = {name: django.forms.ModelChoiceField for name in self.m2m_filter_args}
            fields_dict = fields_for_model(_model, fields=self.m2m_filter_args, field_classes=field_classes)

            for formfield in fields_dict.values():
                formfield.required = False

            if self.m2m_filter_initial:
                _instance = self.instance
                for field, v in self.m2m_filter_initial.items():
                    initial_value = getattr(_instance, v)
                    if initial_value is None:
                        raise KeyError("The instance's attr %s should be not None." % v)

                    fields_dict[field].initial = initial_value

            return (formfield.get_bound_field(self, field) for field, formfield in fields_dict.items())

        else:
            raise KeyError('filter_args need inherit ModelForm.')

    def is_disabled(self):
        if hasattr(self, 'disabled_fields'):
            if self.m2m_filed in self.disabled_fields and self.m2m_filed not in self.disabled_exclude:
                return True
        return False


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

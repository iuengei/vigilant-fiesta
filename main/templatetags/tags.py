from django import template
from django.forms.models import ModelForm
from django.core.urlresolvers import reverse
from django.db.models.fields.related import ForeignObject
from django.db.models.fields.related_descriptors import ManyToManyDescriptor

register = template.Library()


@register.simple_tag
def render_field_display(obj, field):
    field_obj = obj._meta.get_field(field)
    if isinstance(field_obj, ForeignObject):
        value = getattr(obj, field)
    else:
        if field_obj.choices:
            value = getattr(obj, 'get_%s_display' % field)()
        else:
            value = obj.__dict__[field]
        if type(value).__name__ == 'datetime':
            value = value.strftime("%Y-%m-%d %H:%M")
    return value


@register.simple_tag
def render_field_value(obj, field):
    field_obj = obj._meta.get_field(field)
    if isinstance(field_obj, ForeignObject):
        value = getattr(obj, field).pk
    else:
        value = getattr(obj, field)
    return value


@register.simple_tag
def render_field_verbosename(model_or_form, field):
    model = model_or_form._meta.model if isinstance(model_or_form, ModelForm) else model_or_form
    return model._meta.get_field(field).verbose_name


@register.simple_tag
def render_delete_url(model, pk):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    url = reverse('delete', args=(app_label, model_name, pk))
    return url


@register.simple_tag
def render_change_url(model, pk):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    view_name = app_label + ':' + model_name + '_edit'
    url = reverse(view_name, args=(pk,))
    return url


@register.simple_tag
def render_add_url(model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    view_name = app_label + ':' + model_name + '_add'
    url = reverse(view_name)
    return url


@register.simple_tag
def render_detail_url(model, pk):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    view_name = app_label + ':' + model_name
    url = reverse(view_name, args=(pk,))
    return url


@register.simple_tag
def render_message_html(tree):
    html = '<ul>'
    html += tree.message
    html += recursive_children(tree)
    html += '</ul>'
    return html


def recursive_children(tree):
    html = '<ul>'
    while tree.children:
        current = tree.children.pop(0)
        html += '<li>' + current.message
        html += recursive_children(current) + '</li>'
    while tree.m2m_children:
        current = tree.m2m_children.pop(0)
        html += '<li>' + current.message + '</li>'
    html += '</ul>'
    return html


@register.simple_tag
def render_m2m_dict(form, field_name):
    model = form._meta.model
    filter_args = form.m2m_filter_args
    field = form[field_name]
    field_obj = getattr(model, field.name)

    queryset = form.fields[field.name].queryset
    field_value = field.value()
    result = {}

    for each in filter_args:
        each_obj = getattr(field_obj.rel.to, each)

        if isinstance(each_obj, ManyToManyDescriptor):

            _list = [field_obj.rel.to._meta.object_name.lower() + '_id',
                     each_obj.rel.to._meta.object_name.lower() + '_id']
            field_values = each_obj.through.objects.values_list(*_list)
            each_dict = {}
            for item in field_values:
                if item[0] in each_dict:
                    each_dict[item[0]] = each_dict[item[0]] + '-' + str(item[1])
                else:
                    each_dict[item[0]] = str(item[1])
            result[each] = each_dict

    if field_value is None:
        opt_selected = []
        opt_choices = queryset.select_related()
    else:
        opt_selected = queryset.filter(id__in=field_value).select_related()
        opt_choices = queryset.exclude(id__in=field_value).select_related()

    result['selected'] = opt_selected
    result['choices'] = opt_choices
    return result


@register.simple_tag
def render_obj_value(obj, m2m_dict, field):

    value = getattr(obj, field)

    if hasattr(value, 'pk'):
        value = value.pk
    elif 'ManyRelated' in value.__repr__():
        _dict = m2m_dict[field]
        value = _dict[obj.id] if obj.id in _dict else ''

    return value


@register.simple_tag
def render_model_name(model):
    return model._meta.model_name


@register.simple_tag
def render_perm_check(request, obj, action='add', perm=None):
    pk = obj.pk
    opts = obj._meta
    app_label = opts.app_label
    perm = perm if perm else app_label + "." + action + "_" + opts.model_name

    return request.user.perm_obj.has_perm(perm, obj) if pk else \
        (perm in request.user.get_group_permissions() or request.user.has_perm(perm, obj=obj))

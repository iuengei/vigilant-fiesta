from django.db.models import Q
from django.db.models.fields.related import ForeignObject


class SearchQuerySet(object):
    def __init__(self, query_sets, search_content, list_field=None):
        self.query_sets = query_sets
        self.search_content = self.get_search_list(search_content)
        self.model = query_sets.model
        self.opts = query_sets.model._meta
        self.list_field = self.get_fields(list_field)

    @staticmethod
    def get_search_list(content):
        if isinstance(content, str):
            return content.split(' ')
        elif isinstance(content, list):
            return content
        else:
            return list(content)

    def get_fields(self, list_field):
        if list_field == '__all__' or list_field is None:
            _list = [i.name for i in self.opts.local_fields if i.name != 'id']
            return _list
        else:
            return list_field

    @staticmethod
    def get_choices_value(model, field, content):
        choices = model._meta.get_field(field).choices
        if choices:
            for each in choices:
                if content in each[1]:
                    return each[0]
        return None

    def search_q(self, field, content, related=True):
        """生成字段查询条件"""
        field_obj = self.opts.get_field(field)
        field_name = field_obj.name
        if isinstance(field_obj, ForeignObject):
            if related:
                to_model = field_obj.rel.to
                to_fields_list = [i.name for i in to_model._meta.local_fields if i.name != 'id']
                _q = None
                for each in to_fields_list:
                    _ = self.get_choices_value(to_model, each, content)
                    if _:
                        each_obj = to_model._meta.get_field(each)
                        each_name = each_obj.name
                        if not isinstance(each_obj, ForeignObject):
                            _dict = {field_name + '__' + each_name + '__contains': _}
                            if _q:
                                con = Q(**_dict)
                                _q.add(con, Q.OR)
                            else:
                                _q = Q(**_dict)

                if _q and _q.children:
                    return _q
                else:
                    return None
            else:
                return None
        else:
            _ = self.get_choices_value(self.model, field, content)
            if _:
                field_name += '__contains'
                _dict = {field_name: _}
                _q = Q(**_dict)
                return _q
            else:
                return None

    def search_for(self):
        """返回查询的Q对象"""
        search_for = None
        for each in self.search_content:
            con = None
            for field in self.list_field:
                field_q = self.search_q(field, each)
                if field_q and field_q.children:
                    if con:
                        con.add(field_q, Q.OR)
                    else:
                        con = field_q
            if search_for:
                search_for.add(con, Q.AND)
            else:
                search_for = con
        return search_for

    def result(self):
        """返回查询结果的Queryset对象"""
        return self.query_sets.filter(self.search_for()) if self.search_for() else self.query_sets

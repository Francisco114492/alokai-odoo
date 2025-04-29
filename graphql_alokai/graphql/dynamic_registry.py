import graphene

from odoo import models
from pprint import pprint

#from odoo.addons.graphql_alokai.graphql.registry import query_registry, mutation_registry, type_registry
from my_addon_project.alokai_addons.graphql_base import OdooObjectType
from my_addon_project.alokai_odoo.graphql_alokai.graphql.registry import query_registry, mutation_registry, type_registry

class DynamicQuery(models.AbstractModel):
    _name='dynamic.query'
    _description='Criação automática da query'

    @staticmethod
    def resolve_fields(fields, type_cls, mut_cls, resolver=None):
        print(f"Antes: campos em {type_cls.__name__} = {list(type_cls._meta.fields.keys())}")

        # returns 2 dictionaries with fields and resolvers to add
        fields_dict, resolver_dict = DynamicQuery._get_properties_dict(fields)

        for field_name, field in type_cls._meta.fields.items():
            print(f"- {field_name}: {type_cls(field)}")
        #type_registry.remove(type_cls)

        for cls in type_registry:
            print(f"{cls.__name__} != {type_cls.__name__}")
            if cls == type_cls:
                for field in fields_dict:
                    field_type = graphene.Field(fields_dict[field])
                    print(f'field={field} type={fields_dict[field]} / {field_type} cls={cls.__name__}')
                    setattr(type_cls, field, field_type)
                    type_cls._meta.fields[field] = field_type
            if resolver:
                for field in resolver_dict:
                    print(f'field={field} type={resolver_dict[field]} cls={cls.__name__}')
                    setattr(cls, f"resolve_{field}", resolver_dict[field])
        '''
        for field in fields_dict:
            pprint(f'field={field} type={fields_dict[field]}')
            for cls in type_registry:
                if cls == type_cls:
                    field_type = graphene.Field(fields_dict[field])
                    print(f'field={field} type={fields_dict[field]} / {field_type} cls={cls.__name__}')
                    setattr(type_cls, field, field_type)
                    type_cls._meta.fields[field] = field_type

        
                for cls in query_registry:
                    if cls == mut_cls:'''

        #type_registry.append(type_cls)
        #for field_name, field in type_cls._meta.fields.items():
            #print(f"- {field_name}: {type_cls(field)}")
        print(f"Depois: campos em {type_cls.__name__} = {list(type_cls._meta.fields.keys())}")


    def _get_properties_dict(fields):
        fields_dict = {}
        resolver_dict = {}
        for field_name, fld_type in fields.items():
            if fld_type in ('char', 'html', 'text', 'selection'):
                fields_dict[field_name] = graphene.String(required=False)
            elif fld_type in ('float', 'monetary'):
                fields_dict[field_name] = graphene.Float()
            elif fld_type == 'integer':
                fields_dict[field_name] = graphene.Int()
            elif fld_type == 'many2one':
                fields_dict[field_name] = graphene.Field(lambda: OdooObjectType)
            elif fld_type in ('one2many', 'many2many'):
                fields_dict[field_name] = graphene.List(lambda: OdooObjectType)

            resolver_dict[field_name] = DynamicQuery._generate_resolver_method(field_name)

        return fields_dict, resolver_dict

    def _generate_resolver_method(field_name):
        @staticmethod
        def resolver_method(parent, info, field_name=field_name):
            return getattr(parent, field_name, None)

        return resolver_method

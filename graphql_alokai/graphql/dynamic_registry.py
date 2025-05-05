from odoo import models, api
import graphene
from odoo.addons.graphql_base import OdooObjectType

class DynamicQueryMixin(models.AbstractModel):
    _name = 'dynamic.query.mixin'
    _description = 'Mixin para criação automática da query'
    _abstract = True

    @api.model
    @api.model
    def get_graphql_fields_and_resolvers(self):
        fields_dict = {}
        resolver_dict = {}

        model_cls = type(self)

        graphql_fields = getattr(model_cls, '_graphql_fields', {})

        if isinstance(graphql_fields, list):
            graphql_fields = {name: True for name in graphql_fields}

        for field_name, config in graphql_fields.items():
            field = self._fields.get(field_name)
            if not field:
                continue

            # Configuração
            if isinstance(config, dict):
                add_resolver = config.get('res', True)
            elif isinstance(config, bool):
                add_resolver = config

            gfield = self._map_field_to_graphene(field)
            if gfield:
                fields_dict[field_name] = gfield
                resolver_dict[field_name] = self._generate_resolver_method(field_name)

        return fields_dict, resolver_dict

    def _map_field_to_graphene(self, field):
        if field.type in ('char', 'html', 'text', 'selection'):
            return graphene.String(description=field.string)
        elif field.type in ('float', 'monetary'):
            return graphene.Float(description=field.string)
        elif field.type == 'integer':
            return graphene.Int(description=field.string)
        elif field.type == 'many2one':
            # Criar um tipo específico para o modelo relacionado
            related_model = field.comodel_name.replace('.', '_')
            return graphene.Field(
                type(related_model, (OdooObjectType,), {
                    'id': graphene.ID(required=True),
                    'name': graphene.String(),
                    'Meta': type('Meta', (), {
                        'name': related_model,
                        'description': f'Type for {field.comodel_name}'
                    })
                })
            )
        elif field.type in ('one2many', 'many2many'):
            # Criar um tipo específico para a lista de modelos relacionados
            related_model = field.comodel_name.replace('.', '_')
            return graphene.List(
                type(related_model, (OdooObjectType,), {
                    'id': graphene.ID(required=True),
                    'name': graphene.String(),
                    'Meta': type('Meta', (), {
                        'name': related_model,
                        'description': f'Type for {field.comodel_name}'
                    })
                })
            )
        elif field.type == 'boolean':
            return graphene.Boolean(description=field.string)
        elif field.type == 'date':
            return graphene.String(description=field.string)
        elif field.type == 'datetime':
            return graphene.String(description=field.string)
        return None

    def _generate_resolver_method(self, field_name):
        def resolver(parent, info):
            return getattr(parent, field_name, None)
        return resolver

    def update_graphql_type(self, model_name, target_class):
        """
        Atualiza a classe GraphQL, adicionando campos e resolvers definidos em _graphql_fields.
        """
        # Obtém os campos e resolvers definidos no modelo
        print(f"Antes: campos em {target_class.__name__} = {list(target_class._meta.fields.keys())}")
        env=self.env
        fields_dict, resolvers = env[model_name].get_graphql_fields_and_resolvers()

        # Obtém os campos já existentes no tipo GraphQL
        existing_fields = set()
        if hasattr(target_class, '_meta') and hasattr(target_class._meta, 'fields'):
            existing_fields = set(target_class._meta.fields.keys())

        for name, field in fields_dict.items():
            if name in existing_fields: # verifica a existencia do campo no  graphql
                continue
            if not isinstance(field, graphene.Field):
                field = graphene.Field(field)
            # Adiciona o campo à classe
            self.add_field_to_type(target_class, name, field)

            # Adiciona o resolver se estiver definido
            resolver = resolvers.get(name)
            if resolver:
                setattr(target_class, f'resolve_{name}', resolver)
        print(f"Depois: campos em {target_class.__name__} = {list(target_class._meta.fields.keys())}")
        return target_class

    def add_field_to_type(self, type_obj, field_name, field_type, resolver=None):
        """
        Adiciona um novo campo ao tipo GraphQL, sem afetar os campos existentes.
        :param type_obj: O tipo GraphQL (por exemplo, `BlogPost`).
        :param field_name: O nome do campo a ser adicionado.
        :param field_type: O tipo do campo (por exemplo, `graphene.String()`).
        :param resolver: A função que resolve o valor do campo (opcional).
        """
        # Adiciona o campo ao tipo, se ele não existir
        if not hasattr(type_obj, field_name):
            # Adiciona o campo à classe (o tipo GraphQL)
            setattr(type_obj, field_name, field_type)

            # Adiciona o resolver (se fornecido)
            if resolver:
                setattr(type_obj, f"resolve_{field_name}", resolver)

            # Adiciona o campo à _meta.fields (para facilitar busca e manutenção)
            if hasattr(type_obj, '_meta') and hasattr(type_obj._meta, 'fields'):
                type_obj._meta.fields[field_name] = field_type

# Alternativa para fazer campos many2one, many2many e one2many, funciona melhor que o atual, só tenho de indicar qual o modelo
        '''
        elif field.type == 'many2one':
            # Criar um tipo específico para o modelo relacionado
            related_model = field.comodel_name.replace('.', '_')
            return graphene.Field(
                type(related_model, (OdooObjectType,), {
                    'id': graphene.ID(required=True),
                    'name': graphene.String(),
                    'Meta': type('Meta', (), {
                        'name': related_model,
                        'description': f'Type for {field.comodel_name}'
                    })
                })
            )
        elif field.type in ('one2many', 'many2many'):
            # Criar um tipo específico para a lista de modelos relacionados
            related_model = field.comodel_name.replace('.', '_')
            return graphene.List(
                type(related_model, (OdooObjectType,), {
                    'id': graphene.ID(required=True),
                    'name': graphene.String(),
                    'Meta': type('Meta', (), {
                        'name': related_model,
                        'description': f'Type for {field.comodel_name}'
                    })
                })
            )
            '''
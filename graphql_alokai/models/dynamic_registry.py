from odoo import models, api
import graphene
from odoo.addons.graphql_base import OdooObjectType
import logging

_logger = logging.getLogger(__name__)

class DynamicFieldsMixin(models.AbstractModel):
    _name = 'dynamic.query.mixin'
    _description = 'Mixin para criação automática da query'
    _abstract = True

    @api.model
    def get_graphql_fields_and_resolvers(self):
        '''
        Returns dictionaries of GraphQL fields and their corresponding resolvers for the current model.
        Fields are determined by the _graphql_fields attribute of the model.

        :return: Tuple containing:
                - fields_dict: Dictionary mapping field names to their GraphQL field types
                - resolver_dict: Dictionary mapping field names to their resolver methods
        '''
        fields_dict = {}
        resolver_dict = {}

        model_cls = type(self)

        graphql_fields = getattr(model_cls, '_graphql_fields', {})

        if isinstance(graphql_fields, list):
            graphql_fields = {name: True for name in graphql_fields}

        for field_name, config in graphql_fields.items():
            field = self._fields.get(field_name)
            if not field:
                _logger.warning(f'{model_cls._name} has no field {field_name}')
                continue

            # if the add resolver status is {res:True} or just True
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
        '''
        :param field: the field type to be mapped to graphene type
        :return: the graphene type
        '''
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

    def update_graphql_type(self, model_name):
        """
        Main function, calls the functions to gets the graphene type based on the field type, and the resolver.
        Also calls the function to add to the OdooObjectType.
        """

        # Obtém os campos e resolvers definidos no modelo
        target_class = self.env[model_name]._graphql_type
        if not target_class:
            _logger.warning(f'Target class to add field was not provided for {model_name}. Skipping.')
            return
        if not isinstance(target_class, type) or not issubclass(target_class, OdooObjectType):
            _logger.warning(f'Target class {target_class} provided was not of a valid type. Skipping.')
            return

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

            resolver = resolvers.get(name)
            if resolver:
                setattr(target_class, f'resolve_{name}', resolver)
        print(f"Depois: campos em {target_class.__name__} = {list(target_class._meta.fields.keys())}")
        return target_class

    def add_field_to_type(self, type_obj, field_name, field_type, resolver=None):
        """
        Adds new field to the OdooObjectType class
        :param type_obj: OdooObjectType class where the field needs to be added.
        :param field_name: field name to be added.
        :param field_type: graphene type of the field to be added.
        :param resolver: the resolver if it needs to be added.
        """
        if not hasattr(type_obj, field_name):
            setattr(type_obj, field_name, field_type)

            if resolver:
                setattr(type_obj, f"resolve_{field_name}", resolver)

            if hasattr(type_obj, '_meta') and hasattr(type_obj._meta, 'fields'):
                type_obj._meta.fields[field_name] = field_type

    def _get_subclasses(self):
        '''
        Obtains the classes that inherit from the current class.
        '''
        mixin_name = self._name
        result = []
        for model_name in self.env:
            model = self.env[model_name]
            model_cls = type(model)
            inherits = getattr(model_cls, '_inherit', [])
            if isinstance(inherits, str):
                inherits = [inherits]
            if mixin_name in inherits or issubclass(model_cls, self.__class__):
                result.append(model_name)
        return result

    def _register_hook(self):
        '''
        To execute the functions when the module is loaded.
        '''
        super()._register_hook()
        if self._name == 'dynamic.query.mixin': # avoid executing the function for the mixin itself
            return
        sub_cls=self._get_subclasses()
        for cls in sub_cls:
            self.update_graphql_type(cls)

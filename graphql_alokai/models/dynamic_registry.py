
import graphene
import logging

from odoo import models, api
from odoo.addons.graphql_base import OdooObjectType
from ..graphql.registry import type_registry, query_registry, mutation_registry, add_or_replace



_logger = logging.getLogger(__name__)

class DynamicFieldsMixin(models.AbstractModel):
    _name = 'dynamic.registry.mixin'
    _description = 'Mixin para criação automática da query'
    _abstract = True

    def update_graphql_type(self, model_name):
        target_class = getattr(self.env[model_name], '_graphql_type', None)
        target_class_input = getattr(self.env[model_name], '_graphql_filter_input', None)

        target_class = self.verify_class(target_class, model_name, '_graphql_type')
        target_class_input = self.verify_class_input(target_class_input, model_name,'_graphql_filter_input')

        if not target_class:
            return
        print(f"Antes campos em {target_class.__name__} = {list(target_class._meta.fields.keys())}")
        if target_class_input:
            print(f'InputField depois em {target_class_input.__name__} = {list(target_class_input._meta.fields.keys())}')

        fields_dict, resolvers = self.env[model_name].get_graphql_fields_and_resolvers()
        existing_fields = set(getattr(target_class._meta, 'fields', {}).keys())

        for name, field in fields_dict.items():
            if name not in existing_fields:
                new_field = graphene.Field(field) if not isinstance(field, graphene.Field) else field
                self.add_field_to_type(target_class, name, new_field)

            # Só adiciona ao filter input se o campo tiver essa flag
            if getattr(self.env[model_name], "_graphql_fields", {}).get(name, {}).get(
                    'filter_input') and target_class_input:
                self.add_field_to_filter_input(target_class_input, name, field)

            if getattr(self.env[model_name], "_graphql_fields", {}).get(name, {}).get('res'):
                resolver = resolvers.get(name)
                if resolver:
                    setattr(target_class, f'resolve_{name}', resolver)

        print(f"Depois: campos em {target_class.__name__} = {list(target_class._meta.fields.keys())}")
        if target_class_input:
            print(f'InputField depois em {target_class_input.__name__} = {list(target_class_input._meta.fields.keys())}')
        return target_class

    @staticmethod
    def verify_class_input(cls, model_name, attr_name, ):
        if not cls:
            _logger.warning(f'{attr_name} for {model_name} doesn\'t exist. Skipping.')
            return None
        if isinstance(cls, str):
            qry_cls_name=f"{cls}Query"
            class_name = f"{cls}FilterInput"
            target_class = type(class_name, (graphene.InputObjectType,), {})
            qry_cls = type(qry_cls_name, (graphene.ObjectType,), {
                f"{model_name.replace('.', '_')}_list": graphene.List(
                    graphene.String,  # ou qualquer tipo de saída real
                    filters=graphene.Argument(target_class)
                ),
                f"resolve_{model_name.replace('.', '_')}_list": lambda *_: ["Exemplo"]
            })
            add_or_replace(query_registry, [qry_cls])
            return target_class
        if not issubclass(cls, graphene.InputObjectType):
            _logger.warning(f'{attr_name} {cls} for {model_name} is not a subclass of InputObjectType. Skipping.')
            return None
        return cls

    def verify_class(self, cls, model_name, attr_name):
        '''
        Verify the existance of cls and if it's a subclass of exp_type
        :param cls: the class to be verified
        :param model_name: the name of the model from which the fields come from
        :param exp_type: OdooObjectType
        :param attr_name:
        :return: the target class if it's valid or a new one if doesn't exist
        '''
        model_cls = type(self.env[model_name])
        if not isinstance(cls, type):
            _logger.info(f"{attr_name} for {model_name} doesn't exist. Creating.")
            class_base = "".join(part.capitalize() for part in model_name.split("."))
            class_name = f"{class_base}Type"
            target_class = type(class_name, (OdooObjectType,), {})
            setattr(model_cls, attr_name, target_class)
            add_or_replace(type_registry,target_class)
            return target_class
        if not issubclass(cls, OdooObjectType):
            _logger.warning(f'{attr_name} {cls} for {model_name} is not a subclass of {OdooObjectType}. Skipping.')
            return None
        return cls

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

    def add_field_to_filter_input(self, target_class, field_name, field_type):
        '''
        Adds new field to the InputObjectType class
        :param target_class: InputObjectType class where the field needs to be added.
        :param field_name: field name to be added.
        :param field_type: graphene type of the field to be added.
        '''
        if isinstance(field_type, graphene.Field):
            base_type = field_type._type
        else:
            base_type = field_type

            # Verifica se é um tipo de input GraphQL válido
        if not (isinstance(base_type, type) and issubclass(base_type, graphene.InputObjectType)) \
                and not isinstance(base_type, graphene.Scalar):
            _logger.warning(f'Field "{field_name}" with type {base_type} is not a valid GraphQL input type. Skipping.')
            return

        input_field = graphene.InputField(base_type)
        target_class._meta.fields[field_name] = input_field

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
        if self._name == 'dynamic.registry.mixin': # avoid executing the function for the mixin itself
            return
        sub_cls=self._get_subclasses()
        from ..graphql.registry import type_registry, mutation_registry, query_registry
        for cls in sub_cls:
            self.update_graphql_type(cls)

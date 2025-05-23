from odoo import models, fields
from odoo.addons.graphql_alokai.schemas.objects import Company
from odoo.addons.graphql_alokai.models.dynamic_registry import DynamicFieldsMixin




class ExtendedCompany(models.Model, DynamicFieldsMixin):
    _name = 'res.company'
    _inherit = ['res.company', 'dynamic.registry.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes_2 = fields.Integer(string="Internal Notes")

    _graphql_fields = { # the fields to be added and wether a resolver is needed
        "other_author_name": {"resolver": True, 'filter_input':True},  # expose field to graphql with resolver
        "internal_notes_2": {"resolver": False, 'filter_input':False},  # expose field to graphql without resolver
        "teaser": {"resolver": True, 'filter_input':False}
    }
    _graphql_type = Company # the OdooObjectType class where the graphene fields will be added
    _graphql_filter_input = 'ok'
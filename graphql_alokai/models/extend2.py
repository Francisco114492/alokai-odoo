from odoo import models, fields
from ..schemas.objects import Company
from .dynamic_registry import DynamicFieldsMixin




class ExtendedCompany(models.Model, DynamicFieldsMixin):
    _name = 'res.company'
    _inherit = ['res.company', 'dynamic.query.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes_2 = fields.One2many('website',string="Internal Notes")

    _graphql_fields = { # the fields to be added and wether a resolver is needed
        "other_author_name": True,  # expose field to graphql with resolver
        "internal_notes_2": False,  # expose field to graphql without resolver
        "teaser": {"res": True}  # campo herdado, mas adiciona o resolver
        # vai dar warning porque não há campo teaser na company
    }
    _graphql_type = Company # the OdooObjectType class where the graphene fields will be added


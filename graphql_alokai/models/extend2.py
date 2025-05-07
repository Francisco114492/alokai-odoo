from odoo import models, fields
from ..schemas.objects import Company
from .dynamic_registry import DynamicQueryMixin


class ExtendedBlogPost(models.Model, DynamicQueryMixin):
    _name = 'res.company'
    _inherit = ['res.company', 'dynamic.query.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes_2 = fields.One2many('website',string="Internal Notes")

    _graphql_fields = {
        "other_author_name": True,  # expõe o campo com resolver
        "internal_notes_2": {"res": False},  # expõe o campo sem resolver
        "teaser": {"res": True}  # campo herdado, mas adiciona o resolver
    }
    def _register_hook(self):
        super(ExtendedBlogPost, self)._register_hook()
        self.update_graphql_type( 'res.company', Company)




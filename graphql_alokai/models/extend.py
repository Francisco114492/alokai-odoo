from odoo import models, fields, api
from ..schemas.objects import BlogPost
from ..graphql.dynamic_registry import DynamicQueryMixin


class ExtendedBlogPost(models.Model, DynamicQueryMixin):
    _name = 'blog.post'
    _inherit = ['blog.post', 'dynamic.query.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes = fields.Many2many(string="Internal Notes")

    _graphql_fields = {
        "other_author_name": True,  # expõe o campo com resolver
        "internal_notes": {"res": False},  # expõe o campo sem resolver
        "teaser": {"res": True}  # campo herdado, mas adiciona o resolver
    }
    @api.model
    def _register_hook(self):
        res = super(ExtendedBlogPost, self)._register_hook()
        self.setup_graphql_type()
        return res

    def setup_graphql_type(self):
        self.update_graphql_type( 'blog.post', BlogPost)

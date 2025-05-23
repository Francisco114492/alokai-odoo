from odoo import models, fields
from odoo.addons.graphql_alokai.schemas.objects import BlogPost
from odoo.addons.graphql_alokai.schemas.website_blog import BlogPostFilterInput
from odoo.addons.graphql_alokai.models.dynamic_registry import DynamicFieldsMixin



class ExtendedBlogPost(models.Model, DynamicFieldsMixin):
    _name = 'blog.post'
    _inherit = ['blog.post', 'dynamic.registry.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes = fields.Integer(string="Internal Notes")

    _graphql_fields = { # the fields to be added and wether a resolver is needed
        "other_author_name": {"resolver": 'resolve_other_author_name', 'filter_input':True},  # expose field to graphql with resolver
        "internal_notes": {"resolver": False, 'filter_input':False},  # expose field to graphql without resolver
        "teaser": {"resolver": True, 'filter_input':False}  # field already exists, we just add the resolver
    }
    _graphql_type = BlogPost# the OdooObjectType class where the graphene fields will be added
    _graphql_filter_input = BlogPostFilterInput

    def resolve_other_author_name(self):
        return f'{self.author_id.name}qq'

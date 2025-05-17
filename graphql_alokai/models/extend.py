'''from odoo import models, fields

from .dynamic_registry import DynamicFieldsMixin



class ExtendedBlogPost(models.Model, DynamicFieldsMixin):
    _name = 'blog.post'
    _inherit = ['blog.post', 'dynamic.query.mixin']
    other_author_name = fields.Char(string="Other Author Name")
    internal_notes = fields.One2many('website',string="Internal Notes")

    _graphql_fields = { # the fields to be added and wether a resolver is needed
        "other_author_name": True,  # expose field to graphql with resolver
        "internal_notes": False,  # expose field to graphql without resolver
        "teaser": {"res": True}  # field already exists, we just add the resolver
    }
    #_graphql_type = '' # the OdooObjectType class where the graphene fields will be added
    #_graphql_filter_input = BlogPostFilterInput'''
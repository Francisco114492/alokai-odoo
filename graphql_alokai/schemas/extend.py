from odoo import models, fields
from ..schemas.objects import BlogPost
from ..schemas.website_blog import BlogPostSortInput
from ..graphql.dynamic_registry import DynamicQuery

class ExtendedBlogPost():

    type_cls = BlogPost
    qry_cls = BlogPostSortInput
    auto_fields = {'other_author_name': 'char'}
    res=True
    DynamicQuery.resolve_fields(
        fields=auto_fields,
        type_cls=type_cls,
        mut_cls=qry_cls,
        resolver=res
    )
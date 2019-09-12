import os
import base64
import tempfile
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter
from colorthief import ColorThief
from django.conf import settings
from wagtail.search.index import class_is_indexed
from wagtail.search.models import Query
from wagtail.search.backends import get_search_backend
from wagtail.core.models import Page
from wagtail.core.rich_text import RichText


def resolve_queryset(
    qs, info, limit=None, offset=None, search_query=None, id=None, order=None, **kwargs
):
    """
    Add limit, offset and search capabilities to the query. This contains
    argument names used by
    :class:`~wagtail_graphql.types.structures.QuerySetList`.
    :param qs: Query set to be modified.
    :param info: Graphene's info object.
    :param limit: Limit number of objects in the QuerySet.
    :type limit: int
    :param id: Filter by the primary key.
    :type limit: int
    :param offset: Omit a number of objects from the beggining of the query set
    :type offset: int
    :param search_query: Using wagtail search exclude objects that do not match
                         the search query.
    :type search_query: str
    :param order: Use Django ordering format to order the query set.
    :type order: str
    """
    offset = int(offset or 0)

    if id is not None:
        qs = qs.filter(pk=id)

    if id is None and search_query:
        # Check if the queryset is searchable using Wagtail search.
        if not class_is_indexed(qs.model):
            raise TypeError("This data type is not searchable by Wagtail.")

        if settings.GRAPPLE_ADD_SEARCH_HIT is True:
            query = Query.get(search_query)
            query.add_hit()

        return get_search_backend().search(search_query, qs)

    if order is not None:
        qs = qs.order_by(*map(lambda x: x.strip(), order.split(",")))

    if limit is not None:
        limit = int(limit)
        qs = qs[offset : limit + offset]

    return qs


def serialize_rich_text(source):
    # Convert raw pseudo-HTML RichText source to a soup object
    # so it can be manipulated.
    soup = BeautifulSoup(source, 'html.parser')

    # Add data required to generate page links in Gatsby.
    for anchor in soup.find_all('a'):
        if anchor.attrs.get('linktype', '') == 'page':
            try:
                pages = Page.objects.live().public()
                page = pages.get(pk=anchor.attrs['id']).specific
                page_type = page.__class__.__name__

                new_tag = soup.new_tag(
                    'a',
                    href=page.get_url(),

                    # Add dataset arguments to allow processing links on
                    # the front-end.
                    **{
                        'data-page-type': page_type,
                        'data-page-slug': page.slug,
                        'data-page-url': page.url or page.url_path,
                        'href': page.url or page.url_path
                    }
                )
                new_tag.append(*anchor.contents)
                anchor.replace_with(new_tag)
            except Page.DoesNotExist:
                # If page does not exist, add empty anchor tag with text.
                new_tag = soup.new_tag('a')
                new_tag.append(*anchor.contents)
                anchor.replace_with(new_tag)

    # Convert raw pseudo-HTML RichText into a front-end RichText
    return str(RichText(str(soup)))
    
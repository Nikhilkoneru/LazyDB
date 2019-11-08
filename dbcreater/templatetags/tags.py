from django import template
from cloudbackend import settings

register = template.Library()


@register.simple_tag
def get_setting(url):
    return settings.server_url

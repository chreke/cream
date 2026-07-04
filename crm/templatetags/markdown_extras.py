import markdown as md
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(value):
    """Render Markdown to HTML, with raw HTML escaped (not interpreted)."""
    if not value:
        return ""
    return mark_safe(md.markdown(escape(value)))

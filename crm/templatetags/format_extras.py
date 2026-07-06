from django import template

register = template.Library()


@register.filter
def sek(value):
    """Format a money amount as Swedish kronor: 100000 -> "100 000 kr".

    Whole kronor with non-breaking thousand separators; None renders as
    an en dash, like other empty fields.
    """
    if value is None:
        return "–"
    return f"{value:,.0f}".replace(",", "\xa0") + " kr"

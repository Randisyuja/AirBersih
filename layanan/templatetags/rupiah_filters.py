from django import template

register = template.Library()


@register.filter
def rupiah(value):
    """
    Format angka ke format Rupiah: Rp150.000,00
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value  # kalau bukan angka, kembalikan apa adanya

    return "Rp{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

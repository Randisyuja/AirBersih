from django import template

register = template.Library()


@register.filter
def rupiah(value):
    """
    Format angka ke format Rupiah: Rp150.000,00
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value  # kalau bukan angka, kembalikan apa adanya

    return "Rp{:,}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

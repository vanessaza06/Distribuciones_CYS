from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="cop")
def cop(valor):
    """Formatea un monto como pesos colombianos: $80.000 (sin decimales, punto de miles)."""
    try:
        entero = int(Decimal(str(valor if valor is not None else 0)).to_integral_value())
    except (InvalidOperation, ValueError, TypeError):
        entero = 0
    return f"${entero:,}".replace(",", ".")

from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect


class SoporteForm(forms.Form):
    asunto = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control ayd-input", "placeholder": "Asunto"}),
    )
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control ayd-input", "rows": 4, "placeholder": "Cuéntanos tu duda..."}),
    )


# ── Contenido de ayuda (se edita aquí) ──
CATEGORIAS = {
    "ventas": {"nombre": "Ventas", "icono": "bi-cart-fill"},
    "compras": {"nombre": "Compras", "icono": "bi-bag-fill"},
    "inventario": {"nombre": "Inventario", "icono": "bi-box-seam-fill"},
    "devoluciones": {"nombre": "Devoluciones", "icono": "bi-arrow-return-left"},
}

GUIAS = [
    {"cat": "ventas", "titulo": "Cómo registrar una venta",
     "contenido": "Ve a Ventas, elige el cliente, agrega los productos y confirma el pago."},
    {"cat": "compras", "titulo": "Cómo crear una orden de compra",
     "contenido": "Ve a Compras, selecciona el proveedor, agrega los productos y guarda la orden."},
    {"cat": "inventario", "titulo": "Cómo consultar el stock",
     "contenido": "Entra a Inventario para ver las existencias de cada producto."},
    {"cat": "devoluciones", "titulo": "Cómo registrar una devolución",
     "contenido": "Ve a Devoluciones, busca la venta original, elige el motivo y confirma."},
]

FAQS = [
    {"cat": "ventas", "titulo": "¿Puedo anular una venta?",
     "contenido": "Sí, desde el detalle de la venta, si tienes permisos para hacerlo."},
    {"cat": "devoluciones", "titulo": "¿Se restaura el stock en una devolución?",
     "contenido": "Sí, si marcas la opción de restaurar stock al registrar la devolución."},
    {"cat": "inventario", "titulo": "¿Por qué no me aparece un producto?",
     "contenido": "Verifica que el producto esté activo y que lo estés buscando por su nombre correcto."},
    {"cat": "compras", "titulo": "¿Cómo recibo una orden de compra?",
     "contenido": "Abre la orden y confirma la recepción para que el stock se actualice."},
]


def _armar(items, inicio=1):
    lista = []
    for i, it in enumerate(items, start=inicio):
        cat = CATEGORIAS[it["cat"]]
        lista.append({
            "pk": i,
            "titulo": it["titulo"],
            "contenido": it["contenido"],
            "cat_slug": it["cat"],
            "categoria": cat["nombre"],
            "icono": cat["icono"],
        })
    return lista


def index(request):
    if request.method == "POST":
        form = SoporteForm(request.POST)
        if form.is_valid():
            messages.success(request, "Tu mensaje fue enviado. Te responderemos pronto.")
            return redirect("ayuda_index")
    else:
        form = SoporteForm()

    guias = _armar(GUIAS)
    faqs = _armar(FAQS, inicio=100)

    categorias = []
    for slug, cat in CATEGORIAS.items():
        total = sum(1 for x in GUIAS + FAQS if x["cat"] == slug)
        categorias.append({"pk": slug, "nombre": cat["nombre"], "icono": cat["icono"], "total": total})

    return render(request, "ayuda/ayuda.html", {
        "form": form,
        "categorias": categorias,
        "total_articulos": len(GUIAS) + len(FAQS),
        "guias": guias,
        "faqs": faqs,
    })
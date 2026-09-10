from decimal import Decimal
from django import forms
from app.models import (
    Proveedor, Compra, Producto, Lote, Categoria, PresentacionProducto,
    AgendaInventario, Hallazgo,
)


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'nombre_empresa',
            'nit_proveedores',
            'correo',
            'telefono',
            'tipo_proveedor',
            'observacion'
        ]
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control prod-input', 'required': True}),
            'nit_proveedores': forms.TextInput(attrs={'class': 'form-control prod-input', 'required': True}),
            'correo': forms.EmailInput(attrs={'class': 'form-control prod-input', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control prod-input'}),
            'tipo_proveedor': forms.Select(attrs={'class': 'form-select prod-input'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control prod-input', 'rows': 3}),
        }


class NuevaCompraForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'required': True}),
        label="Producto"
    )
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label="Lote (Opcional)"
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 10', 'required': True}),
        label="Cantidad"
    )
    precio_unitario = forms.DecimalField(
        min_value=Decimal('0.01'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej: 25000', 'required': True}),
        label="Precio Unitario"
    )
#-----PRODUCTO-----#

class ProductoRegistroForm(forms.ModelForm):
    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion', 'fecha_vencimiento', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class':       'np-input',
                'placeholder': 'Ej: Cerveza Club Colombia',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'np-input',
                'rows':  2,
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'np-input',
                'type':  'date',
            }),
            'categoria': forms.Select(attrs={
                'class': 'np-input',
            }),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion', 'fecha_vencimiento', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class':       'gp-input',
                'placeholder': 'Ej: Cerveza Club Colombia',
            }),
            'descripcion': forms.Textarea(attrs={
                'class':       'gp-input',
                'rows':        2,
                'placeholder': 'Descripción opcional…',
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'gp-input',
                'type':  'date',
            }),
            'categoria': forms.Select(attrs={
                'class': 'gp-input',
            }),
        }
#-----PRESENTACION-----#

class PresentacionForm(forms.ModelForm):
    class Meta:
        model  = PresentacionProducto
        fields = ['nombre', 'cantidad', 'precio_venta', 'observaciones']
        widgets = {
            'nombre':        forms.TextInput(attrs={'class': 'gp-input', 'placeholder': 'Ej: Six-pack'}),
            'cantidad':      forms.NumberInput(attrs={'class': 'gp-input', 'min': '1'}),
            'precio_venta':  forms.NumberInput(attrs={'class': 'gp-input', 'min': '0', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'gp-input', 'rows': 2}),
        }

#-----LOTE-----#

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = [
            'numero_lote',
            'producto',
            'presentacion',
            'bodega',
            'cantidad_inicial',
            'costo_unitario',
        ]
        widgets = {
            'numero_lote': forms.TextInput(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'presentacion': forms.Select(attrs={'class': 'form-select'}),
            'bodega': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

#-----BODEGA-----#

class AgendaInventarioForm(forms.ModelForm):
    class Meta:
        model = AgendaInventario
        # Solo los campos que el usuario llena en el formulario.
        # documento_usuario, estado y completado_por los asigna la vista, no van aquí.
        fields = ['titulo', 'fecha', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control inv-input', 'placeholder': 'Ej: Inventario mensual Junio'}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control inv-input', 'type': 'datetime-local'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control inv-input', 'rows': 3}),
        }


class HallazgoForm(forms.ModelForm):
    class Meta:
        model = Hallazgo
        # agenda la asigna la vista (hallazgo.agenda = agenda), no va aquí.
        fields = ['producto', 'tipo_hallazgo']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'tipo_hallazgo': forms.Select(attrs={'class': 'form-select'}),
        }
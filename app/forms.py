from decimal import Decimal
from django import forms
from app.models import Proveedor, Producto, Lote
from django import forms
from .models import Producto
from app.models import Categoria
from app.models import PresentacionProducto



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
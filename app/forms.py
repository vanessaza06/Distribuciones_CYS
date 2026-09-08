from decimal import Decimal
from django import forms
from app.models import Proveedor, Producto, Lote


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

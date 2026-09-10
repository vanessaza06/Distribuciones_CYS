from decimal import Decimal
from django import forms
from app.models import Proveedor, Producto, Lote, AgendaInventario, Hallazgo


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


class AgendaInventarioForm(forms.ModelForm):
    class Meta:
        model = AgendaInventario
        fields = [
            'titulo',
            'descripcion',
            'fecha',
            'tipo',
            'estado',
            'responsable',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
        }


class HallazgoForm(forms.ModelForm):
    class Meta:
        model = Hallazgo
        fields = [
            'producto',
            'cantidad_sistema',
            'cantidad_fisica',
            'sesion_conteo',
            'resultado_inventario',
            'observaciones',
        ]
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_sistema': forms.NumberInput(attrs={'class': 'form-control'}),
            'cantidad_fisica': forms.NumberInput(attrs={'class': 'form-control'}),
            'sesion_conteo': forms.TextInput(attrs={'class': 'form-control'}),
            'resultado_inventario': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
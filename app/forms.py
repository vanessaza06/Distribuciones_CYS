from decimal import Decimal
from django import forms
from app.models import Proveedor, Compra, Producto, Lote, Categoria, PresentacionProducto
from app.models import DetalleProducto


#-----DETALLE PRODUCTO-----#
class DetalleProductoForm(forms.ModelForm):
    class Meta:
        model = DetalleProducto
        fields = ['codigo_barras', 'marca', 'fecha_vencimiento', 'descripcion']
        widgets = {
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 7702001234567',
            }),
            'marca': forms.Select(attrs={
                'class': 'form-select',
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del detalle (opcional)…',
            }),
        }

#-----PROVEEDOR-----#
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

#-----COMPRA-----#
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
        from .models import DetalleProducto
        
        
#-----CATEGORIA-----#
class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['codigo', 'nombre', 'descripcion', 'subcategoria']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: CAT-001',
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cervezas',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción opcional…',
            }),
            'subcategoria': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, una categoría no puede aparecer como su propia opción de subcategoria
        if self.instance and self.instance.pk:
            self.fields['subcategoria'].queryset = Categoria.objects.exclude(pk=self.instance.pk)

    def clean_subcategoria(self):
        subcategoria = self.cleaned_data.get('subcategoria')
        if subcategoria and self.instance.pk and subcategoria.pk == self.instance.pk:
            raise forms.ValidationError('Una categoría no puede ser subcategoría de sí misma.')
        return subcategoria


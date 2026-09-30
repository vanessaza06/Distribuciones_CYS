from decimal import Decimal
from django import forms
from django.utils import timezone
from app.models import (
    Proveedor, Compra, Producto, Lote, Categoria, PresentacionProducto,
    AgendaInventario,
)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo marcas activas para elegir
        if 'marca' in self.fields:
            self.fields['marca'].queryset = self.fields['marca'].queryset.model.objects.filter(estado='activo')

    def clean_fecha_vencimiento(self):
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha and fecha < timezone.now().date():
            raise forms.ValidationError('La fecha de vencimiento no puede estar en el pasado.')
        return fecha

    def clean_codigo_barras(self):
        codigo = self.cleaned_data.get('codigo_barras', '').strip()
        if not codigo:
            raise forms.ValidationError('El código de barras es obligatorio.')
        qs = DetalleProducto.objects.filter(codigo_barras=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ese código de barras ya está registrado.')
        return codigo

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
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'formCompraProveedor'}),
        label="Proveedor"
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'required': True, 'id': 'formCompraProducto'}),
        label="Producto"
    )
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'formCompraLote'}),
        label="Lote (Opcional)"
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ej: 10', 'required': True, 'id': 'formCompraCantidad'}),
        label="Cantidad"
    )
    precio_unitario = forms.DecimalField(
        min_value=Decimal('0.01'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'placeholder': 'Ej: 25000', 'required': True, 'id': 'formCompraPrecio'}),
        label="Precio Unitario ($)"
    )
    estado = forms.ChoiceField(
        choices=[
            ('pendiente', 'Pendiente de entrega'),
            ('confirmada', 'Confirmada'),
            ('recibida', 'Recibida (Ingresar a inventario)'),
        ],
        initial='recibida',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'formCompraEstado'}),
        label="Estado de Compra"
    )
    numero_factura = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ej: FAC-2026-001', 'id': 'formCompraFactura'}),
        label="N° Factura / Referencia (Opcional)"
    )
    monto_pagado = forms.DecimalField(
        min_value=Decimal('0.00'),
        decimal_places=2,
        required=False,
        initial=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01', 'placeholder': '0 para crédito total', 'id': 'formCompraPago'}),
        label="Abono Inicial ($)"
    )
    metodo_pago = forms.ChoiceField(
        choices=[
            ('efectivo', 'Efectivo'),
            ('nequi', 'Nequi'),
            ('daviplata', 'Daviplata'),
            ('bancolombia', 'Bancolombia'),
            ('breb', 'Bre-B'),
        ],
        initial='efectivo',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'formCompraMetodoPago'}),
        label="Método de Pago"
    )
#-----PRODUCTO-----#

class ProductoRegistroForm(forms.ModelForm):
    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class':       'np-input',
                'placeholder': 'Ej: Cerveza Club Colombia',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'np-input',
                'rows':  2,
            }),
            'categoria': forms.Select(attrs={
                'class': 'np-input',
            }),
        }


class ProductoForm(forms.ModelForm):
    class Meta:
        model  = Producto
        fields = ['nombre', 'descripcion','categoria']
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
            'precio_venta':  forms.NumberInput(attrs={'class': 'gp-input', 'min': '0.01', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'gp-input', 'rows': 2}),
        }
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad < 1:
            raise forms.ValidationError('La cantidad debe ser 1 o más.')
        return cantidad

    def clean_precio_venta(self):
        precio = self.cleaned_data.get('precio_venta')
        if precio is None or precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio


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
            'cantidad_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bodega'].required = False
        
    def clean_cantidad_inicial(self):
        cantidad = self.cleaned_data.get('cantidad_inicial')
        if cantidad is None or cantidad < 1:
            raise forms.ValidationError('La cantidad inicial debe ser 1 o más.')
        return cantidad

    def clean_costo_unitario(self):
        costo = self.cleaned_data.get('costo_unitario')
        if costo is None or costo <= 0:
            raise forms.ValidationError('El costo unitario debe ser mayor a 0.')
        return costo

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get('producto')
        presentacion = cleaned.get('presentacion')
        if producto and presentacion and presentacion.producto_id != producto.pk:
            self.add_error('presentacion', 'Esta presentación no pertenece al producto seleccionado.')
        return cleaned
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


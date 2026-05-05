from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.forms import inlineformset_factory

from .models import Order, OrderItem, Product, ProductSupply, ProductVariant, Supply, UserAccess

User = get_user_model()


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control')
                widget.attrs.setdefault('rows', 3)
            else:
                widget.attrs.setdefault('class', 'form-control')


class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'description', 'is_active', 'stock']
        labels = {
            'name': 'Nombre',
            'category': 'Categoría',
            'price': 'Precio',
            'description': 'Descripción',
            'is_active': 'Activo',
            'stock': 'Existencia inicial',
        }


class SupplyForm(StyledModelForm):
    class Meta:
        model = Supply
        fields = ['name', 'is_available']
        labels = {
            'name': 'Nombre',
            'is_available': 'Hay existencia',
        }


class ProductVariantForm(StyledModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'name', 'price_delta', 'stock', 'is_active']
        labels = {
            'product': 'Producto',
            'name': 'Variante',
            'price_delta': 'Agregado al precio',
            'stock': 'Existencia',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['product'].empty_label = 'Selecciona un producto'


class ProductVariantEditForm(StyledModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'price_delta', 'stock', 'is_active']
        labels = {
            'name': 'Variante',
            'price_delta': 'Agregado al precio',
            'stock': 'Existencia',
            'is_active': 'Activo',
        }


class ProductSupplyForm(StyledModelForm):
    class Meta:
        model = ProductSupply
        fields = ['product', 'supply']
        labels = {
            'product': 'Producto',
            'supply': 'Insumo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['product'].empty_label = 'Selecciona un producto'
        self.fields['supply'].queryset = Supply.objects.all()
        self.fields['supply'].empty_label = 'Selecciona un insumo'


class OrderForm(StyledModelForm):
    class Meta:
        model = Order
        fields = ['table_number', 'notes']
        labels = {
            'table_number': 'Número de mesa',
            'notes': 'Notas',
        }


class OrderItemForm(StyledModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'diner_name', 'quantity', 'notes']
        labels = {
            'product': 'Producto',
            'diner_name': 'Comensal',
            'quantity': 'Cantidad',
            'notes': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['product'].empty_label = 'Selecciona un producto'


class BaseOrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        has_item = False
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('product') and form.cleaned_data.get('quantity'):
                has_item = True
        if not has_item:
            raise forms.ValidationError('Agrega al menos un producto a la comanda.')


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    formset=BaseOrderItemFormSet,
    extra=4,
    can_delete=True,
)


class UserAccessMixin:
    access_field_labels = {
        'can_menu': 'Acceso a Menu',
        'can_administrador': 'Acceso a Administrador',
        'can_comanda': 'Acceso a Comanda',
        'can_cocina': 'Acceso a Cocina',
        'can_bar': 'Acceso a Bar',
        'can_entregas': 'Acceso a Entregas',
        'can_caja': 'Acceso a Caja',
    }
    access_field_names = [
        'can_menu',
        'can_administrador',
        'can_comanda',
        'can_cocina',
        'can_bar',
        'can_entregas',
        'can_caja',
    ]

    def ensure_access_fields(self):
        if 'role' not in self.fields:
            self.fields['role'] = forms.ChoiceField(choices=UserAccess.RoleChoices.choices, label='Rol')
        for field_name in self.access_field_names:
            if field_name not in self.fields:
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=self.access_field_labels[field_name],
                )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ensure_access_fields()
        for field_name in self.access_field_names + ['role']:
            field = self.fields[field_name]
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

        profile = None
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.access_profile
            except UserAccess.DoesNotExist:
                profile = None
        if profile:
            self.initial.setdefault('role', profile.role)
            for field_name in self.access_field_names:
                self.initial.setdefault(field_name, getattr(profile, field_name))
        else:
            self.initial.setdefault('role', UserAccess.RoleChoices.EMPLEADO)
            self.initial.setdefault('can_menu', True)

    def save_access_profile(self, user):
        profile, _ = UserAccess.objects.get_or_create(user=user)
        role = self.cleaned_data['role']
        profile.role = role
        for field_name in self.access_field_names:
            setattr(profile, field_name, self.cleaned_data.get(field_name, False))

        if role == UserAccess.RoleChoices.ADMINISTRADOR:
            for field_name in self.access_field_names:
                setattr(profile, field_name, True)

        profile.save()


class UserCreateForm(UserAccessMixin, StyledModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo',
            'is_active': 'Activo',
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        if password1:
            validate_password(password1)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            self.save_access_profile(user)
        return user


class UserUpdateForm(UserAccessMixin, StyledModelForm):
    new_password = forms.CharField(
        label='Nueva contraseña (opcional)',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo',
            'is_active': 'Activo',
        }

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_access_profile(user)
        return user


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-lg'
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ClientProfile, Product, ClientProduct, ContactRequest

class ClientProductInline(admin.TabularInline):
    model = ClientProduct
    extra = 0
    fields = ('product', 'status', 'monthly_cost', 'start_date', 'end_date', 'notes')

class ClientProfileInline(admin.StackedInline):
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Cliente'
    inlines = [ClientProductInline]

class CustomUserAdmin(UserAdmin):
    inlines = (ClientProfileInline,)
    list_display = ('username', 'email', 'company_name', 'is_client', 'is_active', 'tenant_id')
    list_filter = UserAdmin.list_filter + ('is_client',)
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('tenant_id', 'company_name', 'phone', 'is_client')}),
    )
    readonly_fields = ('tenant_id',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'status', 'created_at')
    list_filter = ('product_type', 'status', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'get_products_count')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__company_name', 'user__email')
    inlines = [ClientProductInline]
    
    def get_products_count(self, obj):
        return obj.products.count()
    get_products_count.short_description = 'Productos'

@admin.register(ClientProduct)
class ClientProductAdmin(admin.ModelAdmin):
    list_display = ('client', 'product', 'status', 'monthly_cost', 'start_date')
    list_filter = ('status', 'product__product_type', 'start_date')
    search_fields = ('client__user__username', 'product__name')
    date_hierarchy = 'start_date'

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'empresa', 'status', 'newsletter', 'created_at')
    list_filter = ('status', 'newsletter', 'created_at')
    search_fields = ('nombre', 'email', 'empresa', 'proyecto')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información de Contacto', {
            'fields': ('nombre', 'email', 'empresa')
        }),
        ('Consulta', {
            'fields': ('proyecto', 'newsletter')
        }),
        ('Seguimiento', {
            'fields': ('status', 'notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    tenant_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company_name = models.CharField(max_length=255, blank=True, verbose_name="Empresa")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    is_client = models.BooleanField(default=True, verbose_name="Es cliente")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.username} - {self.company_name}"

class Product(models.Model):
    PRODUCT_TYPES = [
        ('chatbot', 'Chatbot'),
        ('web_simple', 'Web Simple'),
        ('suit_commerce', 'Suit Commerce'),
        ('automation', 'Automatización RPA'),
        ('data_migration', 'Migración de Datos'),
        ('custom_development', 'Desarrollo a Medida'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('maintenance', 'En Mantenimiento'),
        ('discontinued', 'Discontinuado'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Nombre del Producto")
    product_type = models.CharField(
        max_length=50,
        choices=PRODUCT_TYPES,
        verbose_name="Tipo de Producto"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Estado"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"

class ClientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    website_url = models.URLField(blank=True, verbose_name="URL del sitio web")
    products = models.ManyToManyField(
        Product,
        through='ClientProduct',
        verbose_name="Productos/Servicios"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Perfil de Cliente"
        verbose_name_plural = "Perfiles de Clientes"
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

class ClientProduct(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('cancelled', 'Cancelado'),
        ('development', 'En Desarrollo'),
    ]
    
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Estado"
    )
    start_date = models.DateField(auto_now_add=True, verbose_name="Fecha de Inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin")
    monthly_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo Mensual"
    )
    notes = models.TextField(blank=True, verbose_name="Notas del Servicio")
    
    class Meta:
        verbose_name = "Producto del Cliente"
        verbose_name_plural = "Productos del Cliente"
        unique_together = ['client', 'product']
    
    def __str__(self):
        return f"{self.client.user.username} - {self.product.name}"


class ContactRequest(models.Model):
    """Modelo para guardar las consultas del formulario de contacto"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('contacted', 'Contactado'),
        ('converted', 'Convertido'),
        ('discarded', 'Descartado'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Email")
    empresa = models.CharField(max_length=200, blank=True, verbose_name="Empresa")
    proyecto = models.TextField(verbose_name="Proyecto")
    newsletter = models.BooleanField(default=False, verbose_name="Suscripción Newsletter")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Estado"
    )
    notes = models.TextField(blank=True, verbose_name="Notas internas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de consulta")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    class Meta:
        verbose_name = "Consulta de Contacto"
        verbose_name_plural = "Consultas de Contacto"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre} - {self.email} ({self.get_status_display()})"


# Crear automáticamente el perfil cuando se crea un usuario cliente
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_client_profile(sender, instance, created, **kwargs):
    if created and instance.is_client:
        ClientProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_client_profile(sender, instance, **kwargs):
    if instance.is_client and hasattr(instance, 'clientprofile'):
        instance.clientprofile.save()
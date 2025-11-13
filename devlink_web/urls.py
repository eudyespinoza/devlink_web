from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from accounts.views import login_view, logout_view, dashboard_view, whatsapp_report_client, edit_questions_client

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('portal/', login_view, name='portal'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/whatsapp-report/', whatsapp_report_client, name='whatsapp_report_client'),
    path('dashboard/edit-questions/', edit_questions_client, name='edit_questions_client'),
    path('admin-panel/', include('admin_panel.urls')),
    
    # Páginas estáticas existentes
    path('aviso-iluminacion/', TemplateView.as_view(template_name='aviso-iluminacion.html'), name='aviso_iluminacion'),
    path('documentacion/', TemplateView.as_view(template_name='documentacion.html'), name='documentacion'),
    path('email-bienvenida/', TemplateView.as_view(template_name='email-bienvenida.html'), name='email_bienvenida'),
    path('email-preview/', TemplateView.as_view(template_name='email-preview.html'), name='email_preview'),
    path('politicas-privacidad/', TemplateView.as_view(template_name='politicas-privacidad.html'), name='politicas_privacidad'),
    path('terminos-servicio/', TemplateView.as_view(template_name='terminos-servicio.html'), name='terminos_servicio'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
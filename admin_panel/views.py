from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Q
from accounts.models import CustomUser, ClientProfile, Product, ClientProduct
from django.contrib.auth import get_user_model
from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime

User = get_user_model()

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def admin_dashboard(request):
    total_users = User.objects.filter(is_client=True).count()
    active_users = User.objects.filter(is_client=True, is_active=True).count()
    recent_users = User.objects.filter(is_client=True).order_by('-date_joined')[:5]
    total_products = Product.objects.count()
    active_products = Product.objects.filter(status='active').count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'recent_users': recent_users,
        'total_products': total_products,
        'active_products': active_products,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@user_passes_test(is_superuser)
def users_list(request):
    search_query = request.GET.get('search', '')
    users = User.objects.filter(is_client=True)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/users_list.html', context)

@user_passes_test(is_superuser)
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name', '')
        phone = request.POST.get('phone', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'admin_panel/user_form.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'admin_panel/user_form.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            company_name=company_name,
            phone=phone,
            is_client=True
        )
        
        # El perfil se crea automáticamente por la señal
        
        messages.success(request, f'Usuario {username} creado exitosamente. Tenant ID: {user.tenant_id}')
        return redirect('/admin-panel/users/')
    
    return render(request, 'admin_panel/user_form.html')

@user_passes_test(is_superuser)
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.company_name = request.POST.get('company_name', '')
        user.phone = request.POST.get('phone', '')
        user.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        
        # Actualizar perfil
        profile = user.clientprofile
        profile.website_url = request.POST.get('website_url', '')
        profile.notes = request.POST.get('notes', '')
        profile.save()
        
        messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
        return redirect(f'/admin-panel/users/{user.id}/edit/')
    
    # Obtener productos del usuario y productos disponibles
    user_products = ClientProduct.objects.filter(client=user.clientprofile).select_related('product')
    assigned_product_ids = user_products.values_list('product_id', flat=True)
    available_products = Product.objects.filter(status='active').exclude(id__in=assigned_product_ids)
    
    context = {
        'user_obj': user,
        'user_products': user_products,
        'available_products': available_products,
    }
    return render(request, 'admin_panel/user_edit.html', context)

@user_passes_test(is_superuser)
def add_user_product(request, user_id):
    user = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        status = request.POST.get('status', 'active')
        
        product = get_object_or_404(Product, id=product_id)
        
        # Verificar que el producto no esté ya asignado
        if not ClientProduct.objects.filter(client=user.clientprofile, product=product).exists():
            ClientProduct.objects.create(
                client=user.clientprofile,
                product=product,
                status=status
            )
            messages.success(request, f'Producto "{product.name}" agregado exitosamente.')
        else:
            messages.error(request, f'El producto "{product.name}" ya está asignado al usuario.')
    
    return redirect(f'/admin-panel/users/{user.id}/edit/')

@user_passes_test(is_superuser)
def update_user_product_status(request, user_id):
    user = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        client_product_id = request.POST.get('client_product_id')
        status = request.POST.get('status')
        
        client_product = get_object_or_404(ClientProduct, id=client_product_id, client=user.clientprofile)
        client_product.status = status
        client_product.save()
        
        messages.success(request, f'Estado del producto "{client_product.product.name}" actualizado.')
    
    return redirect(f'/admin-panel/users/{user.id}/edit/')

@user_passes_test(is_superuser)
def remove_user_product(request, user_id):
    user = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        client_product_id = request.POST.get('client_product_id')
        
        client_product = get_object_or_404(ClientProduct, id=client_product_id, client=user.clientprofile)
        product_name = client_product.product.name
        client_product.delete()
        
        messages.success(request, f'Producto "{product_name}" eliminado del usuario.')
    
    return redirect(f'/admin-panel/users/{user.id}/edit/')

@user_passes_test(is_superuser)
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Usuario {username} eliminado exitosamente.')
        return redirect('/admin-panel/users/')
    
    context = {'user_obj': user}
    return render(request, 'admin_panel/user_confirm_delete.html', context)

# ============= PRODUCTOS =============

@user_passes_test(is_superuser)
def products_list(request):
    search_query = request.GET.get('search', '')
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(product_type__icontains=search_query)
        )
    
    products = products.order_by('-created_at')
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/products_list.html', context)

@user_passes_test(is_superuser)
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        product_type = request.POST.get('product_type')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'active')
        
        if Product.objects.filter(name=name).exists():
            messages.error(request, 'Ya existe un producto con ese nombre.')
            return render(request, 'admin_panel/product_form.html', {
                'product_types': Product.PRODUCT_TYPES,
                'status_choices': Product.STATUS_CHOICES,
            })
        
        Product.objects.create(
            name=name,
            product_type=product_type,
            description=description,
            status=status
        )
        
        messages.success(request, f'Producto "{name}" creado exitosamente.')
        return redirect('/admin-panel/products/')
    
    context = {
        'product_types': Product.PRODUCT_TYPES,
        'status_choices': Product.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/product_form.html', context)

@user_passes_test(is_superuser)
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.product_type = request.POST.get('product_type')
        product.description = request.POST.get('description', '')
        product.status = request.POST.get('status', 'active')
        product.save()
        
        messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
        return redirect('/admin-panel/products/')
    
    # Crear un objeto form-like para el template
    form_data = {
        'name': {'value': product.name},
        'product_type': {'value': product.product_type},
        'description': {'value': product.description},
        'status': {'value': product.status},
    }
    
    context = {
        'object': product,
        'form': type('Form', (), form_data)(),
        'product_types': Product.PRODUCT_TYPES,
    }
    return render(request, 'admin_panel/product_edit.html', context)

@user_passes_test(is_superuser)
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        return redirect('/admin-panel/products/')
    
    context = {'product': product}
    return render(request, 'admin_panel/product_confirm_delete.html', context)

# ============= PRODUCTOS DE CLIENTE =============

@user_passes_test(is_superuser)
def user_products(request, user_id):
    user_obj = get_object_or_404(User, id=user_id, is_client=True)
    client_products = ClientProduct.objects.filter(client=user_obj.clientprofile).select_related('product')
    available_products = Product.objects.filter(status='active').exclude(
        id__in=[cp.product.id for cp in client_products]
    )
    
    context = {
        'user_obj': user_obj,
        'user_products': client_products,
        'available_products': available_products,
    }
    return render(request, 'admin_panel/user_products.html', context)

@user_passes_test(is_superuser)
def add_user_product(request, user_id):
    user_obj = get_object_or_404(User, id=user_id, is_client=True)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        status = request.POST.get('status', 'active')
        monthly_cost = request.POST.get('monthly_cost')
        notes = request.POST.get('notes', '')
        
        product = get_object_or_404(Product, id=product_id)
        
        client_product, created = ClientProduct.objects.get_or_create(
            client=user_obj.clientprofile,
            product=product,
            defaults={
                'status': status,
                'monthly_cost': monthly_cost if monthly_cost else None,
                'notes': notes
            }
        )
        
        if created:
            messages.success(request, f'Producto "{product.name}" agregado al cliente.')
        else:
            messages.warning(request, f'El cliente ya tiene el producto "{product.name}".')
        
        return redirect(f'/admin-panel/users/{user_id}/edit/')
    
    return redirect(f'/admin-panel/users/{user_id}/edit/')

@user_passes_test(is_superuser)
def remove_user_product(request, user_id, product_id):
    user_obj = get_object_or_404(User, id=user_id, is_client=True)
    client_product = get_object_or_404(
        ClientProduct,
        client=user_obj.clientprofile,
        product_id=product_id
    )
    
    if request.method == 'POST':
        product_name = client_product.product.name
        client_product.delete()
        messages.success(request, f'Producto "{product_name}" removido del cliente.')
        return redirect(f'/admin-panel/users/{user_id}/products/')
    
    context = {
        'user_obj': user_obj,
        'client_product': client_product,
    }
    return render(request, 'admin_panel/remove_user_product.html', context)


@user_passes_test(is_superuser)
def whatsapp_report(request, user_id):
    """Vista para el reporte de WhatsApp Basic"""
    user_obj = get_object_or_404(User, id=user_id, is_client=True)
    
    # Conectar a MongoDB (solo lectura)
    try:
        mongo_uri = "mongodb://admin:superseguro123@200.58.107.187:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Verificar conexión
        client.admin.command('ping')
        
        # Obtener la base de datos y colecciones
        db = client['chatbot']
        registros_collection = db['registros']
        menus_collection = db['menus']
        
        # Obtener menús para mapear opciones
        menus = {str(menu.get('id', '')): menu for menu in menus_collection.find({})}
        
        # Estructura para almacenar datos agrupados por opción del menú
        opciones_agrupadas = defaultdict(lambda: {
            'cantidad': 0,
            'usuarios_unicos': set(),
            'ultima_consulta': None,
            'descripcion': ''
        })
        
        # Obtener todos los registros
        documentos = registros_collection.find({})
        
        # Procesar cada documento
        for doc in documentos:
            usuario = doc.get('phone_number', 'Anónimo')
            opcion = doc.get('ultimo_mensaje', '')
            timestamp = doc.get('timestamp', '')
            
            # Buscar descripción de la opción en los menús
            descripcion = f"Opción {opcion}"
            encontrado = False
            
            for menu_id, menu_data in menus.items():
                submenu = menu_data.get('submenu', '')
                
                if not submenu or submenu == 'direct':
                    continue
                
                # Si la opción es un número (1-12), buscar en el menú principal
                if opcion.isdigit():
                    # Para 10, buscar 🔟
                    if opcion == '10' and '🔟' in submenu:
                        for linea in submenu.split('\n'):
                            if '🔟' in linea:
                                descripcion = linea.strip()
                                encontrado = True
                                break
                    # Para 11, buscar 1️⃣1️⃣
                    elif opcion == '11' and '1️⃣1️⃣' in submenu:
                        for linea in submenu.split('\n'):
                            if '1️⃣1️⃣' in linea:
                                descripcion = linea.strip()
                                encontrado = True
                                break
                    # Para 12, buscar 1️⃣2️⃣
                    elif opcion == '12' and '1️⃣2️⃣' in submenu:
                        for linea in submenu.split('\n'):
                            if '1️⃣2️⃣' in linea:
                                descripcion = linea.strip()
                                encontrado = True
                                break
                    # Para 1-9, buscar con emoji número
                    elif (f"{opcion}️⃣" in submenu or f"{opcion}\ufe0f\u20e3" in submenu):
                        for linea in submenu.split('\n'):
                            if linea.strip().startswith(f"{opcion}️⃣") or linea.strip().startswith(f"{opcion}\ufe0f\u20e3"):
                                descripcion = linea.strip()
                                encontrado = True
                                break
                
                # Si la opción es una letra (A, B, C, D), buscar en submenús
                elif opcion.isalpha():
                    # Buscar la letra con formato: [emoji] LETRA - Descripción
                    for linea in submenu.split('\n'):
                        if f" {opcion.upper()} - " in linea or f" {opcion.lower()} - " in linea:
                            descripcion = linea.strip()
                            encontrado = True
                            break
                
                if encontrado:
                    break
            
            # Agrupar por opción
            clave = f"{opcion} - {descripcion}"
            opciones_agrupadas[clave]['cantidad'] += 1
            opciones_agrupadas[clave]['usuarios_unicos'].add(usuario)
            opciones_agrupadas[clave]['descripcion'] = descripcion
            
            # Formatear timestamp si existe
            try:
                if timestamp:
                    # Si timestamp es un string con formato ISO, convertirlo
                    if isinstance(timestamp, str):
                        from datetime import datetime as dt
                        timestamp_dt = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp_formateado = timestamp_dt.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        timestamp_formateado = timestamp
                else:
                    timestamp_formateado = 'N/A'
            except:
                timestamp_formateado = timestamp or 'N/A'
            
            if not opciones_agrupadas[clave]['ultima_consulta'] or timestamp > opciones_agrupadas[clave]['ultima_consulta']:
                opciones_agrupadas[clave]['ultima_consulta'] = timestamp_formateado
        
        # Convertir sets a listas para el template
        preguntas_lista = []
        for clave, datos in opciones_agrupadas.items():
            preguntas_lista.append({
                'pregunta': datos['descripcion'],
                'total_consultas': datos['cantidad'],
                'usuarios_unicos': len(datos['usuarios_unicos']),
                'usuarios_list': list(datos['usuarios_unicos']),
                'ultima_consulta': datos['ultima_consulta']
            })
        
        # Ordenar por cantidad de consultas (de mayor a menor)
        preguntas_lista.sort(key=lambda x: x['total_consultas'], reverse=True)
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(preguntas_lista, 10)  # 10 preguntas por página
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Calcular estadísticas generales
        total_consultas = sum(p['total_consultas'] for p in preguntas_lista)
        total_usuarios_unicos = len(set(u for p in preguntas_lista for u in p['usuarios_list']))
        # Top 10 excluyendo "Volver al menú principal"
        top_10 = [p for p in preguntas_lista if 'volver al menú principal' not in p['pregunta'].lower()][:10]
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Cerrar conexión
        client.close()
        
        context = {
            'user_obj': user_obj,
            'total_consultas': total_consultas,
            'total_preguntas': len(preguntas_lista),
            'total_usuarios_unicos': total_usuarios_unicos,
            'promedio_usuario': round(total_consultas / total_usuarios_unicos, 1) if total_usuarios_unicos > 0 else 0,
            'top_10': top_10,
            'page_obj': page_obj,
            'fecha_reporte': fecha_actual,
        }
        
        return render(request, 'admin_panel/whatsapp_report.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al conectar con MongoDB: {str(e)}')
        return redirect('admin_panel:user_products', user_id=user_id)
        
        # Cerrar conexión
        client.close()
        
        context = {
            'user_obj': user_obj,
            'total_consultas': total_consultas,
            'total_preguntas': len(preguntas_lista),
            'total_usuarios_unicos': total_usuarios_unicos,
            'promedio_usuario': round(total_consultas / total_usuarios_unicos, 1) if total_usuarios_unicos > 0 else 0,
            'top_10': top_10,
            'preguntas_lista': preguntas_lista,
            'fecha_reporte': fecha_actual,
        }
        
        return render(request, 'admin_panel/whatsapp_report.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al conectar con MongoDB: {str(e)}')
        return redirect('admin_panel:user_products', user_id=user_id)
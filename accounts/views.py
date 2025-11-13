from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import CustomUser, ClientProfile, ClientProduct
from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin-panel/')
        else:
            return redirect('/dashboard/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if user.is_superuser:
                    return redirect('/admin-panel/')
                elif user.is_client:
                    return redirect('/dashboard/')
                else:
                    messages.error(request, 'No tiene permisos para acceder al sistema.')
                    return redirect('/portal/')
            else:
                messages.error(request, 'Su cuenta está desactivada.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def dashboard_view(request):
    if not request.user.is_client:
        return redirect('/portal/')
    
    try:
        client_profile = request.user.clientprofile
    except ClientProfile.DoesNotExist:
        client_profile = ClientProfile.objects.create(user=request.user)
    
    # Obtener productos del cliente
    client_products = client_profile.clientproduct_set.filter(status='active').select_related('product')
    
    context = {
        'user': request.user,
        'tenant_id': request.user.tenant_id,
        'client_products': client_products,
        'website_url': client_profile.website_url,
        'is_active': client_profile.is_active,
    }
    return render(request, 'dashboard/main.html', context)


@login_required
def whatsapp_report_client(request):
    """Vista para el reporte de WhatsApp del cliente"""
    if not request.user.is_client:
        return redirect('/portal/')
    
    # Verificar que el cliente tenga un producto chatbot activo
    try:
        client_profile = request.user.clientprofile
        chatbot_product = client_profile.clientproduct_set.filter(
            product__product_type='chatbot',
            status='active'
        ).first()
        
        if not chatbot_product:
            messages.error(request, 'No tienes acceso al reporte de WhatsApp.')
            return redirect('/dashboard/')
    except ClientProfile.DoesNotExist:
        messages.error(request, 'No tienes acceso al reporte de WhatsApp.')
        return redirect('/dashboard/')
    
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
        
        # Convertir sets a listas
        preguntas_lista = []
        for clave, datos in opciones_agrupadas.items():
            preguntas_lista.append({
                'pregunta': datos['descripcion'],
                'total_consultas': datos['cantidad'],
                'usuarios_unicos': len(datos['usuarios_unicos']),
                'usuarios_list': list(datos['usuarios_unicos']),
                'ultima_consulta': datos['ultima_consulta']
            })
        
        preguntas_lista.sort(key=lambda x: x['total_consultas'], reverse=True)
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(preguntas_lista, 10)  # 10 preguntas por página
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas generales
        total_consultas = sum(p['total_consultas'] for p in preguntas_lista)
        total_usuarios_unicos = len(set(u for p in preguntas_lista for u in p['usuarios_list']))
        # Top 10 excluyendo "Volver al menú principal"
        top_10 = [p for p in preguntas_lista if 'volver al menú principal' not in p['pregunta'].lower()][:10]
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        client.close()
        
        context = {
            'user': request.user,
            'total_consultas': total_consultas,
            'total_preguntas': len(preguntas_lista),
            'total_usuarios_unicos': total_usuarios_unicos,
            'promedio_usuario': round(total_consultas / total_usuarios_unicos, 1) if total_usuarios_unicos > 0 else 0,
            'top_10': top_10,
            'page_obj': page_obj,
            'fecha_reporte': fecha_actual,
        }
        
        return render(request, 'dashboard/whatsapp_report.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al conectar con la base de datos: {str(e)}')
        return redirect('/dashboard/')


@login_required
def edit_questions_client(request):
    """Vista para editar preguntas y respuestas del chatbot"""
    if not request.user.is_client:
        return redirect('/portal/')
    
    # Verificar que el cliente tenga un producto chatbot activo
    try:
        client_profile = request.user.clientprofile
        chatbot_product = client_profile.clientproduct_set.filter(
            product__product_type='chatbot',
            status='active'
        ).first()
        
        if not chatbot_product:
            messages.error(request, 'No tienes acceso a la edición de preguntas.')
            return redirect('/dashboard/')
    except ClientProfile.DoesNotExist:
        messages.error(request, 'No tienes acceso a la edición de preguntas.')
        return redirect('/dashboard/')
    
    # Conectar a MongoDB (solo lectura para obtener datos)
    try:
        mongo_uri = "mongodb://admin:superseguro123@200.58.107.187:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Verificar conexión
        client.admin.command('ping')
        
        # Obtener la base de datos y colección de menús
        db = client['chatbot']
        menus_collection = db['menus']
        respuestas_collection = db['respuestas']
        
        # Obtener todos los menús y convertir ObjectId a string
        menus_raw = menus_collection.find({})
        menus = []
        for menu in menus_raw:
            # Convertir ObjectId a string para el template
            if '_id' in menu:
                menu['id'] = str(menu['_id']) if menu.get('id') is None else menu.get('id')
            
            menu_id = menu.get('id', '')
            
            # Si el menú tiene submenu="direct", buscar la respuesta en la colección respuestas
            if menu.get('submenu') == 'direct':
                respuesta = respuestas_collection.find_one({'id': str(menu_id)})
                if respuesta:
                    # Crear una estructura de respuestas similar a los submenús
                    menu['respuestas'] = [{
                        'id': respuesta.get('id', menu_id),
                        'respuesta': respuesta.get('respuesta', '')
                    }]
                else:
                    menu['respuestas'] = []
            # Si tiene submenu con opciones A, B, C, D - buscar respuestas en colección respuestas
            elif menu.get('submenu') and menu.get('submenu') != 'direct':
                submenu = menu.get('submenu', '')
                respuestas_menu = []
                
                # Buscar opciones A-Z en el submenu
                for linea in submenu.split('\n'):
                    # Buscar patrón: [emoji] LETRA - Descripción
                    import re
                    match = re.search(r'\s([A-Z])\s*-\s*(.+)', linea)
                    if match:
                        letra = match.group(1)
                        descripcion = match.group(2).strip()
                        
                        # Buscar la respuesta en la colección con id "menuId+Letra"
                        resp_id = f"{menu_id}{letra}"
                        respuesta_doc = respuestas_collection.find_one({'id': resp_id})
                        
                        if respuesta_doc:
                            respuestas_menu.append({
                                'id': resp_id,
                                'opcion': letra,
                                'descripcion': descripcion,
                                'respuesta': respuesta_doc.get('respuesta', '')
                            })
                
                menu['respuestas'] = respuestas_menu
            else:
                # Asegurar que respuestas sea una lista
                if 'respuestas' not in menu or menu['respuestas'] is None:
                    menu['respuestas'] = []
            
            menus.append(menu)
        
        client.close()
        
        # Generar fecha actual
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        context = {
            'user': request.user,
            'menus': menus,
            'fecha_actual': fecha_actual,
        }
        
        return render(request, 'dashboard/edit_questions.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al conectar con la base de datos: {str(e)}')
        return redirect('/dashboard/')


@login_required
def save_question_client(request):
    """Vista para guardar cambios en respuestas del chatbot"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if not request.user.is_client:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Verificar que el cliente tenga un producto chatbot activo
    try:
        client_profile = request.user.clientprofile
        chatbot_product = client_profile.clientproduct_set.filter(
            product__product_type='chatbot',
            status='active'
        ).first()
        
        if not chatbot_product:
            return JsonResponse({'error': 'No tienes acceso a editar respuestas'}, status=403)
    except ClientProfile.DoesNotExist:
        return JsonResponse({'error': 'No tienes acceso a editar respuestas'}, status=403)
    
    # Obtener datos del formulario
    respuesta_id = request.POST.get('respuesta_id')
    nueva_respuesta = request.POST.get('nueva_respuesta')
    
    if not respuesta_id or not nueva_respuesta:
        return JsonResponse({'error': 'Datos incompletos'}, status=400)
    
    # Conectar a MongoDB y actualizar
    try:
        mongo_uri = "mongodb://admin:superseguro123@200.58.107.187:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Verificar conexión
        client.admin.command('ping')
        
        # Obtener la colección de respuestas
        db = client['chatbot']
        respuestas_collection = db['respuestas']
        
        # Actualizar la respuesta
        resultado = respuestas_collection.update_one(
            {'id': respuesta_id},
            {'$set': {'respuesta': nueva_respuesta}}
        )
        
        client.close()
        
        if resultado.modified_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'Respuesta actualizada correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró la respuesta o no hubo cambios'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al actualizar: {str(e)}'
        }, status=500)
#!/bin/bash

echo "Iniciando despliegue de DevLink..."

# Crear red de Traefik si no existe
docker network create traefik_proxy 2>/dev/null || true

# Construir y levantar servicios
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
sleep 10

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario si no existe
docker-compose exec web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@devlink.com.ar', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
EOF

echo "Despliegue completado!"
echo "Acceso: https://devlink.com.ar"
echo "Admin: https://devlink.com.ar/admin-panel/"
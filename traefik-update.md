# Agregar estas líneas a tu dynamic.yml existente en la sección tls.certificates:

# Para devlink.com.ar agregar:
- certFile: /etc/ssl/devlink/devlink.com.ar.crt
  keyFile: /etc/ssl/devlink/devlink.com.ar.key

# También agregar en CORS si es necesario:
# En accessControlAllowOriginList:
# - "https://devlink.com.ar"
# - "https://www.devlink.com.ar"
# Clínica Mentalmente - Sistema de Agendamiento

Sistema web para agendamiento de citas psicológicas con gestión de consentimientos informados.

## 🚀 Despliegue en Render.com

### Requisitos Previos

1. **Cuenta en Render.com** - Registrarse en [render.com](https://render.com)
2. **Cuenta en GitHub** - Para subir el código
3. **Base de datos PostgreSQL** - Render proporciona PostgreSQL gratuito

### Paso a Paso para Desplegar

#### 1. Preparar el Repositorio

```bash
# Asegúrate de que todos los archivos estén en tu repositorio local
git add .
git commit -m "Preparar para despliegue en Render"
git push origin main
```

#### 2. Crear Cuenta en Render

1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio de GitHub

#### 3. Crear Base de Datos PostgreSQL

1. En el dashboard de Render, haz clic en **"New +"**
2. Selecciona **"PostgreSQL"**
3. Configura:
   - **Name**: `mentalmente-db`
   - **Database**: `mentalmente`
   - **User**: `mentalmente_user`
   - **Plan**: Free
4. Haz clic en **"Create Database"**
5. Guarda la **Connection String** que te proporciona

#### 4. Crear Servicio Web

1. En el dashboard de Render, haz clic en **"New +"**
2. Selecciona **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Configura:
   - **Name**: `mentalmente-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

#### 5. Configurar Variables de Entorno

En la sección **"Environment Variables"** del servicio web, agrega:

```
SECRET_KEY = [generar una clave secreta]
DATABASE_URL = [la connection string de PostgreSQL]
MAIL_SERVER = smtp.gmail.com
MAIL_PORT = 587
MAIL_USE_TLS = true
MAIL_USERNAME = citasmentalmente@gmail.com
MAIL_PASSWORD = [tu contraseña de aplicación de Gmail]
```

#### 6. Migrar Base de Datos

1. Una vez que el servicio esté desplegado, ejecuta el script de migración:

```bash
# En tu máquina local, con la DATABASE_URL configurada
python migrate_to_postgres.py
```

#### 7. Verificar Despliegue

1. Ve a la URL proporcionada por Render
2. Verifica que la aplicación funcione correctamente
3. Prueba el agendamiento de citas

### 🔧 Configuración Local

Para desarrollo local:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones locales

# Ejecutar aplicación
python app.py
```

### 📁 Estructura del Proyecto

```
reto_zasca/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración de la aplicación
├── models.py             # Modelos de base de datos
├── requirements.txt      # Dependencias de Python
├── render.yaml           # Configuración de Render
├── gunicorn.conf.py      # Configuración de Gunicorn
├── Procfile              # Archivo para Render
├── runtime.txt           # Versión de Python
├── migrate_to_postgres.py # Script de migración
├── templates/            # Plantillas HTML
├── static/               # Archivos estáticos (CSS, JS, imágenes)
└── pdfs/                 # PDFs generados
```

### 🔐 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta para sesiones | `mi-clave-secreta-123` |
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@host/db` |
| `MAIL_SERVER` | Servidor SMTP | `smtp.gmail.com` |
| `MAIL_PORT` | Puerto SMTP | `587` |
| `MAIL_USERNAME` | Email para envío | `tu-email@gmail.com` |
| `MAIL_PASSWORD` | Contraseña de aplicación | `tu-contraseña-app` |

### 🚨 Solución de Problemas

#### Error de Base de Datos
- Verifica que la `DATABASE_URL` esté correctamente configurada
- Asegúrate de que las tablas se hayan creado correctamente

#### Error de Email
- Verifica las credenciales de Gmail
- Asegúrate de usar una "Contraseña de aplicación" de Gmail

#### Error de Build
- Verifica que `requirements.txt` esté actualizado
- Revisa los logs de build en Render

### 📞 Soporte

Para problemas específicos del despliegue:
1. Revisa los logs en el dashboard de Render
2. Verifica la configuración de variables de entorno
3. Asegúrate de que todos los archivos estén en el repositorio

### 🔄 Actualizaciones

Para actualizar la aplicación:
1. Haz cambios en tu código local
2. Haz commit y push a GitHub
3. Render automáticamente redeployará la aplicación

---

**Nota**: Este proyecto está configurado para funcionar tanto en desarrollo local (MySQL) como en producción (PostgreSQL en Render). 
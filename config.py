import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración general
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-segura-123')
    APP_NAME = "Mentalmente - Psicología Especializada"
    
    # Configuración de correo 
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'citasmentalmente@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'rehu udfw lakk zuhp')
    MAIL_DEFAULT_SENDER = ('Clínica Mentalmente', MAIL_USERNAME)
    MAIL_DEBUG = os.getenv('MAIL_DEBUG', 'False').lower() == 'true'
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'
    MAIL_TIMEOUT = int(os.getenv('MAIL_TIMEOUT', 30))
    MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', 0)) if os.getenv('MAIL_MAX_EMAILS') else None
    
    # Configuración de base de datos
    # Para desarrollo local usa MySQL, para producción usa PostgreSQL de Render
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    if DATABASE_URL:
        # Producción - PostgreSQL en Render
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        # Configuración específica para PostgreSQL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_timeout': 30,
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'mentalmente_app'
            }
        }
    else:
        # Desarrollo local - MySQL
        SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/mentalmente'
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_timeout': 30,
            'pool_size': 10,
            'max_overflow': 20,
        }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de la aplicación
    UPLOAD_FOLDER = 'pdfs'
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Configuración de tokens
    TOKEN_EXPIRATION_HOURS = 24

    # Configuración de logging para depuración
    LOG_MAIL = True  # Registrar operaciones de correo

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True
    MAIL_DEBUG = True  # Mostrar logs SMTP en desarrollo
    SQLALCHEMY_ECHO = True  # Mostrar consultas SQL

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    MAIL_DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Configuración para producción 
    MAIL_SERVER = os.getenv('PROD_MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('PROD_MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('PROD_MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('PROD_MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('PROD_MAIL_PASSWORD')
    
    # Configuración de seguridad para producción
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
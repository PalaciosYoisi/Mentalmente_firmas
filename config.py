import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración general
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-segura-123')
    APP_NAME = "Mentalmente - Psicología Especializada"
    
    # Configuración de correo 
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'citasmentalmente@gmail.com'
    MAIL_PASSWORD = 'rehu udfw lakk zuhp'
    MAIL_DEFAULT_SENDER = ('Clínica Mentalmente', 'citasmentalmente@gmail.com')
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = False
    MAIL_TIMEOUT = 30
    MAIL_MAX_EMAILS = None
    
    # Configuración de base de datos MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/mentalmente'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'pool_size': 10,
        'max_overflow': 20,
    }
    
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
    # Configuración para producción 
    MAIL_SERVER = os.getenv('PROD_MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = os.getenv('PROD_MAIL_PORT', 587)
    MAIL_USE_TLS = os.getenv('PROD_MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('PROD_MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('PROD_MAIL_PASSWORD')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
from flask_sqlalchemy import SQLAlchemy
from typing import Optional, List
from datetime import datetime, date

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Enum('admin', 'psicologo', 'asistente'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime)
    fecha_actualizacion = db.Column(db.DateTime)
    psicologo = db.relationship('Psicologo', backref='usuario', uselist=False)

    def __init__(self, email: str, password_hash: str, tipo: str, activo: bool = True, fecha_creacion: Optional[datetime] = None, fecha_actualizacion: Optional[datetime] = None):
        self.email = email
        self.password_hash = password_hash
        self.tipo = tipo
        self.activo = activo
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    tipo_identificacion = db.Column(db.Enum('CC','TI','CE','PA'), nullable=False)
    numero_identificacion = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.Enum('Apartadó', 'Medellín', 'Quibdó'), nullable=False)
    fecha_registro = db.Column(db.DateTime)
    citas = db.relationship('Cita', backref='paciente', lazy=True)

    def __init__(self, nombre_completo: str, tipo_identificacion: str, numero_identificacion: str, telefono: str, email: str, fecha_registro: Optional[datetime] = None, fecha_nacimiento: Optional[date] = None, genero: Optional[str] = None, direccion: Optional[str] = None, ciudad: str = 'Apartadó'):
        self.nombre_completo = nombre_completo
        self.tipo_identificacion = tipo_identificacion
        self.numero_identificacion = numero_identificacion
        self.telefono = telefono
        self.email = email
        self.fecha_registro = fecha_registro
        self.fecha_nacimiento = fecha_nacimiento
        self.genero = genero
        self.direccion = direccion
        self.ciudad = ciudad

    def __repr__(self):
        return f'<Paciente {self.nombre_completo}>'

class Psicologo(db.Model):
    __tablename__ = 'psicologos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    numero_identificacion = db.Column(db.String(20), nullable=False)
    especialidad = db.Column(db.String(100))
    firma_digital = db.Column(db.Text)
    telefono = db.Column(db.String(20))
    citas = db.relationship('Cita', backref='psicologo', lazy=True)

    def __init__(self, usuario_id: int, nombre_completo: str, numero_identificacion: str, especialidad: Optional[str] = None, firma_digital: Optional[str] = None, telefono: Optional[str] = None):
        self.usuario_id = usuario_id
        self.nombre_completo = nombre_completo
        self.numero_identificacion = numero_identificacion
        self.especialidad = especialidad
        self.firma_digital = firma_digital
        self.telefono = telefono

class Cita(db.Model):
    __tablename__ = 'citas'
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    psicologo_id = db.Column(db.Integer, db.ForeignKey('psicologos.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    duracion_minutos = db.Column(db.Integer, default=50)
    tipo_consulta = db.Column(db.Enum('primera_vez','control','emergencia'), nullable=False)
    estado = db.Column(db.Enum('pendiente','aceptada','rechazada','completada','cancelada'), default='pendiente')
    token_firma = db.Column(db.String(64), unique=True)
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime)
    consentimiento = db.relationship('Consentimiento', uselist=False, backref='cita')

    def __init__(self, paciente_id: int, psicologo_id: int, fecha_hora: datetime, duracion_minutos: int = 50, tipo_consulta: str = 'primera_vez', estado: str = 'pendiente', token_firma: Optional[str] = None, notas: Optional[str] = None, fecha_creacion: Optional[datetime] = None):
        self.paciente_id = paciente_id
        self.psicologo_id = psicologo_id
        self.fecha_hora = fecha_hora
        self.duracion_minutos = duracion_minutos
        self.tipo_consulta = tipo_consulta
        self.estado = estado
        self.token_firma = token_firma
        self.notas = notas
        self.fecha_creacion = fecha_creacion

class Consentimiento(db.Model):
    __tablename__ = 'consentimientos'
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    firma_paciente = db.Column(db.Text, nullable=False)
    firma_psicologo = db.Column(db.Text)
    ip_paciente = db.Column(db.String(45))
    dispositivo_paciente = db.Column(db.String(255))
    fecha_firma_paciente = db.Column(db.DateTime)
    fecha_firma_psicologo = db.Column(db.DateTime)
    pdf_final = db.Column(db.LargeBinary)
    hash_documento = db.Column(db.String(64), unique=True)

    def __init__(self, cita_id: int, firma_paciente: str, ip_paciente: Optional[str] = None, dispositivo_paciente: Optional[str] = None, fecha_firma_paciente: Optional[datetime] = None, pdf_final: Optional[bytes] = None, firma_psicologo: Optional[str] = None, fecha_firma_psicologo: Optional[datetime] = None, hash_documento: Optional[str] = None):
        self.cita_id = cita_id
        self.firma_paciente = firma_paciente
        self.ip_paciente = ip_paciente
        self.dispositivo_paciente = dispositivo_paciente
        self.fecha_firma_paciente = fecha_firma_paciente
        self.pdf_final = pdf_final
        self.firma_psicologo = firma_psicologo
        self.fecha_firma_psicologo = fecha_firma_psicologo
        self.hash_documento = hash_documento

class Tutor(db.Model):
    __tablename__ = 'tutores'
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    tipo_identificacion = db.Column(db.String(20), nullable=False)
    numero_identificacion = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    ciudad = db.Column(db.String(100), nullable=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False, unique=True)
    paciente = db.relationship('Paciente', backref=db.backref('tutor', uselist=False))

    def __init__(self, nombre_completo, tipo_identificacion, numero_identificacion, email, telefono, ciudad, paciente_id):
        self.nombre_completo = nombre_completo
        self.tipo_identificacion = tipo_identificacion
        self.numero_identificacion = numero_identificacion
        self.email = email
        self.telefono = telefono
        self.ciudad = ciudad
        self.paciente_id = paciente_id 
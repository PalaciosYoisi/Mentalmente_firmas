#!/usr/bin/env python3
"""
Script para migrar la base de datos de MySQL a PostgreSQL
Ejecutar este script después de crear la base de datos PostgreSQL en Render
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def migrate_to_postgres():
    """Migra los datos de MySQL a PostgreSQL"""
    
    # Configuración de MySQL (origen)
    mysql_url = 'mysql+mysqlconnector://root:@localhost/mentalmente'
    
    # Configuración de PostgreSQL (destino)
    postgres_url = os.getenv('DATABASE_URL')
    if not postgres_url:
        print("Error: DATABASE_URL no está configurada")
        return False
    
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Conectar a MySQL
        print("Conectando a MySQL...")
        mysql_engine = create_engine(mysql_url)
        mysql_session = sessionmaker(bind=mysql_engine)()
        
        # Conectar a PostgreSQL
        print("Conectando a PostgreSQL...")
        postgres_engine = create_engine(postgres_url)
        postgres_session = sessionmaker(bind=postgres_engine)()
        
        # Crear tablas en PostgreSQL (esto se hará automáticamente con SQLAlchemy)
        print("Creando tablas en PostgreSQL...")
        
        # Migrar datos de psicólogos
        print("Migrando psicólogos...")
        psicologos = mysql_session.execute(text("SELECT * FROM psicologo")).fetchall()
        for psicologo in psicologos:
            postgres_session.execute(text("""
                INSERT INTO psicologo (id, nombre_completo, especialidad, email, telefono, ciudad, estado)
                VALUES (:id, :nombre_completo, :especialidad, :email, :telefono, :ciudad, :estado)
                ON CONFLICT (id) DO NOTHING
            """), psicologo._asdict())
        
        # Migrar pacientes
        print("Migrando pacientes...")
        pacientes = mysql_session.execute(text("SELECT * FROM paciente")).fetchall()
        for paciente in pacientes:
            postgres_session.execute(text("""
                INSERT INTO paciente (id, nombre_completo, tipo_identificacion, numero_identificacion, 
                                    email, telefono, fecha_nacimiento, genero, direccion, ciudad, modalidad)
                VALUES (:id, :nombre_completo, :tipo_identificacion, :numero_identificacion,
                       :email, :telefono, :fecha_nacimiento, :genero, :direccion, :ciudad, :modalidad)
                ON CONFLICT (id) DO NOTHING
            """), paciente._asdict())
        
        # Migrar citas
        print("Migrando citas...")
        citas = mysql_session.execute(text("SELECT * FROM cita")).fetchall()
        for cita in citas:
            postgres_session.execute(text("""
                INSERT INTO cita (id, paciente_id, psicologo_id, fecha_hora, estado, modalidad, 
                                created_at, updated_at)
                VALUES (:id, :paciente_id, :psicologo_id, :fecha_hora, :estado, :modalidad,
                       :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """), cita._asdict())
        
        # Migrar usuarios
        print("Migrando usuarios...")
        usuarios = mysql_session.execute(text("SELECT * FROM usuario")).fetchall()
        for usuario in usuarios:
            postgres_session.execute(text("""
                INSERT INTO usuario (id, email, password_hash, tipo_usuario, created_at)
                VALUES (:id, :email, :password_hash, :tipo_usuario, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), usuario._asdict())
        
        # Migrar horarios
        print("Migrando horarios...")
        horarios = mysql_session.execute(text("SELECT * FROM horario_psicologo")).fetchall()
        for horario in horarios:
            postgres_session.execute(text("""
                INSERT INTO horario_psicologo (id, psicologo_id, dia_semana, hora_inicio, hora_fin, estado)
                VALUES (:id, :psicologo_id, :dia_semana, :hora_inicio, :hora_fin, :estado)
                ON CONFLICT (id) DO NOTHING
            """), horario._asdict())
        
        # Commit de los cambios
        postgres_session.commit()
        
        print("✅ Migración completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        postgres_session.rollback()
        return False
    
    finally:
        mysql_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate_to_postgres() 
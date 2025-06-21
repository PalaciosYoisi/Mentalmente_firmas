#!/usr/bin/env python3
"""
Script para actualizar la tabla horarios_psicologos
Cambia de dia_semana a fecha específica
"""

from app import app, db
from datetime import datetime, date, timedelta
from models import Psicologo, HorarioPsicologo

def actualizar_tabla_horarios():
    with app.app_context():
        try:
            # Verificar si la columna fecha existe
            result = db.session.execute("SHOW COLUMNS FROM horarios_psicologos LIKE 'fecha'")
            fecha_exists = result.fetchone()
            
            if not fecha_exists:
                print("Agregando columna 'fecha'...")
                db.session.execute("ALTER TABLE horarios_psicologos ADD COLUMN fecha DATE AFTER psicologo_id")
                db.session.commit()
                print("Columna 'fecha' agregada exitosamente.")
            
            # Verificar si la columna dia_semana existe
            result = db.session.execute("SHOW COLUMNS FROM horarios_psicologos LIKE 'dia_semana'")
            dia_semana_exists = result.fetchone()
            
            if dia_semana_exists:
                print("Migrando datos de dia_semana a fecha...")
                
                # Obtener todos los horarios existentes
                result = db.session.execute("SELECT id, psicologo_id, dia_semana, hora_inicio, hora_fin, activo FROM horarios_psicologos WHERE dia_semana IS NOT NULL")
                horarios = result.fetchall()
                
                for horario in horarios:
                    # Convertir dia_semana a fechas futuras (próximas 4 semanas)
                    for semana in range(4):
                        # Calcular la fecha para este día de la semana
                        fecha_base = date.today()
                        dias_hasta_proximo = (horario[2] - fecha_base.weekday()) % 7
                        if dias_hasta_proximo == 0 and semana == 0:
                            dias_hasta_proximo = 7
                        fecha = fecha_base + timedelta(days=dias_hasta_proximo + (semana * 7))
                        
                        # Insertar nuevo horario con fecha específica
                        db.session.execute("""
                            INSERT INTO horarios_psicologos 
                            (psicologo_id, fecha, hora_inicio, hora_fin, activo, fecha_creacion, fecha_actualizacion)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        """, (horario[1], fecha, horario[3], horario[4], horario[5]))
                
                # Eliminar la columna dia_semana
                print("Eliminando columna 'dia_semana'...")
                db.session.execute("ALTER TABLE horarios_psicologos DROP COLUMN dia_semana")
                db.session.commit()
                print("Migración completada exitosamente.")
            else:
                print("La columna 'dia_semana' ya no existe. La migración ya fue completada.")
            
            # Crear índices para mejorar el rendimiento
            print("Creando índices...")
            try:
                db.session.execute("CREATE INDEX idx_psicologo_fecha ON horarios_psicologos(psicologo_id, fecha)")
                db.session.execute("CREATE INDEX idx_fecha_activo ON horarios_psicologos(fecha, activo)")
                db.session.commit()
                print("Índices creados exitosamente.")
            except Exception as e:
                print(f"Los índices ya existen o hubo un error: {e}")
            
            print("¡Actualización de tabla completada exitosamente!")
            
        except Exception as e:
            print(f"Error durante la actualización: {e}")
            db.session.rollback()
            raise

def agregar_fechas_prueba():
    """Agregar fechas de prueba adicionales para múltiples psicólogos"""
    with app.app_context():
        try:
            print("Agregando fechas de prueba adicionales...")
            
            # Obtener todos los psicólogos
            psicologos = Psicologo.query.all()
            
            if not psicologos:
                print("No hay psicólogos en la base de datos.")
                return
            
            # Fechas de prueba (próximas 2 semanas)
            fechas_prueba = []
            for i in range(1, 15):  # 14 días
                fecha = date.today() + timedelta(days=i)
                fechas_prueba.append(fecha)
            
            # Horarios de trabajo típicos
            horarios_trabajo = [
                ('08:00', '12:00'),
                ('14:00', '18:00'),
                ('09:00', '13:00'),
                ('15:00', '19:00'),
                ('10:00', '14:00'),
                ('16:00', '20:00')
            ]
            
            horarios_creados = 0
            
            for psicologo in psicologos:
                print(f"Agregando horarios para {psicologo.nombre_completo}...")
                
                # Para cada psicólogo, agregar horarios en días alternos
                for i, fecha in enumerate(fechas_prueba):
                    if i % 2 == 0:  # Solo días pares para este psicólogo
                        # Seleccionar un horario aleatorio
                        hora_inicio, hora_fin = horarios_trabajo[i % len(horarios_trabajo)]
                        
                        # Verificar si ya existe un horario para esta fecha y psicólogo
                        horario_existente = HorarioPsicologo.query.filter_by(
                            psicologo_id=psicologo.id,
                            fecha=fecha
                        ).first()
                        
                        if not horario_existente:
                            nuevo_horario = HorarioPsicologo(
                                psicologo_id=psicologo.id,
                                fecha=fecha,
                                hora_inicio=datetime.strptime(hora_inicio, '%H:%M').time(),
                                hora_fin=datetime.strptime(hora_fin, '%H:%M').time(),
                                activo=True
                            )
                            db.session.add(nuevo_horario)
                            horarios_creados += 1
                
                # Para el siguiente psicólogo, usar días impares
                for i, fecha in enumerate(fechas_prueba):
                    if i % 2 == 1:  # Solo días impares para el siguiente psicólogo
                        hora_inicio, hora_fin = horarios_trabajo[(i + 1) % len(horarios_trabajo)]
                        
                        horario_existente = HorarioPsicologo.query.filter_by(
                            psicologo_id=psicologo.id,
                            fecha=fecha
                        ).first()
                        
                        if not horario_existente:
                            nuevo_horario = HorarioPsicologo(
                                psicologo_id=psicologo.id,
                                fecha=fecha,
                                hora_inicio=datetime.strptime(hora_inicio, '%H:%M').time(),
                                hora_fin=datetime.strptime(hora_fin, '%H:%M').time(),
                                activo=True
                            )
                            db.session.add(nuevo_horario)
                            horarios_creados += 1
            
            db.session.commit()
            print(f"✅ Se agregaron {horarios_creados} horarios de prueba exitosamente.")
            
        except Exception as e:
            print(f"❌ Error al agregar fechas de prueba: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Ejecutando actualización de tabla de horarios...")
    actualizar_tabla_horarios()
    
    print("\n🔄 Agregando fechas de prueba adicionales...")
    agregar_fechas_prueba()
    
    print("\n✅ Proceso completado exitosamente!") 
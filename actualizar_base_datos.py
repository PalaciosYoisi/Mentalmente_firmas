#!/usr/bin/env python3
"""
Script para actualizar automáticamente el estado de las citas en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Cita, Consentimiento

def actualizar_estados_citas():
    """Actualiza automáticamente el estado de las citas basándose en los consentimientos"""
    
    with app.app_context():
        try:
            print("Iniciando actualización de estados de citas...")
            
            # Buscar citas con estado vacío que tienen consentimientos
            citas_con_consentimiento = db.session.query(Cita).join(
                Consentimiento, Cita.id == Consentimiento.cita_id
            ).filter(Cita.estado == '').all()
            
            print(f"Encontradas {len(citas_con_consentimiento)} citas con consentimientos y estado vacío")
            
            for cita in citas_con_consentimiento:
                consentimiento = Consentimiento.query.filter_by(cita_id=cita.id).first()
                if consentimiento:
                    if consentimiento.firma_psicologo:
                        cita.estado = 'completada'
                        print(f"Cita {cita.id}: Actualizada a 'completada'")
                    else:
                        cita.estado = 'firmado_paciente'
                        print(f"Cita {cita.id}: Actualizada a 'firmado_paciente'")
            
            # Buscar citas con estado vacío que no tienen consentimientos
            citas_sin_consentimiento = db.session.query(Cita).filter(
                Cita.estado == ''
            ).all()
            
            print(f"Encontradas {len(citas_sin_consentimiento)} citas sin consentimientos y estado vacío")
            
            for cita in citas_sin_consentimiento:
                consentimiento = Consentimiento.query.filter_by(cita_id=cita.id).first()
                if not consentimiento:
                    cita.estado = 'aceptada'
                    print(f"Cita {cita.id}: Actualizada a 'aceptada'")
            
            db.session.commit()
            print("✅ Estados de citas actualizados correctamente")
            
            # Mostrar resumen
            print("\n--- RESUMEN DE ESTADOS ---")
            citas = Cita.query.all()
            for cita in citas:
                consentimiento = Consentimiento.query.filter_by(cita_id=cita.id).first()
                tiene_firma_paciente = consentimiento and consentimiento.firma_paciente
                tiene_firma_psicologo = consentimiento and consentimiento.firma_psicologo
                
                print(f"Cita {cita.id}: Estado='{cita.estado}' | Firma Paciente: {tiene_firma_paciente} | Firma Psicólogo: {tiene_firma_psicologo}")
            
        except Exception as e:
            print(f"❌ Error al actualizar estados de citas: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 Ejecutando actualización de base de datos...")
    if actualizar_estados_citas():
        print("✅ Actualización completada exitosamente")
    else:
        print("❌ Error en la actualización")
        sys.exit(1) 
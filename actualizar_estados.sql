-- Script para actualizar estados de citas en la base de datos
-- Ejecutar en phpMyAdmin o cliente MySQL

USE mentalmente;

-- Actualizar cita con ID 1 que tiene consentimientos pero estado vacío
-- Como tiene consentimientos pero el psicólogo no ha firmado, debe ser 'firmado_paciente'
UPDATE citas 
SET estado = 'firmado_paciente' 
WHERE id = 1;

-- Verificar el cambio
SELECT c.id, c.estado, c.paciente_id, c.psicologo_id, 
       con.firma_paciente IS NOT NULL as tiene_firma_paciente,
       con.firma_psicologo IS NOT NULL as tiene_firma_psicologo
FROM citas c
LEFT JOIN consentimientos con ON c.id = con.cita_id
WHERE c.id = 1;

-- Mostrar todas las citas y sus estados
SELECT c.id, c.estado, c.paciente_id, c.psicologo_id, 
       p.nombre_completo as paciente_nombre,
       ps.nombre_completo as psicologo_nombre,
       con.firma_paciente IS NOT NULL as tiene_firma_paciente,
       con.firma_psicologo IS NOT NULL as tiene_firma_psicologo
FROM citas c
LEFT JOIN pacientes p ON c.paciente_id = p.id
LEFT JOIN psicologos ps ON c.psicologo_id = ps.id
LEFT JOIN consentimientos con ON c.id = con.cita_id
ORDER BY c.id; 
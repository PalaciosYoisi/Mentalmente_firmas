from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_mail import Mail, Message
from fpdf import FPDF
from datetime import datetime, date
import base64
import re
import os
import secrets
import logging
from dotenv import load_dotenv
from models import db, Paciente, Psicologo, Cita, Consentimiento, Usuario, Tutor
from typing import List, Tuple, Any, Sequence

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de la aplicación
app = Flask(__name__)
load_dotenv()

# Configuración
app.config.from_object('config.DevelopmentConfig')

# Inicialización de extensiones
db.init_app(app)
mail = Mail(app)

class PDF(FPDF):
    def header(self):
        # Fondo en todas las páginas
        self.image('static/img/fondo_consentimientos.jpg', x=0, y=0, w=self.w, h=self.h)

    def footer(self):
        pass

# --- Funciones de apoyo ---
def enviar_correo_rechazo(cita):
    try:
        msg = Message(
            "Estado de tu cita - Clínica Mentalmente",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[cita.paciente.email]
        )
        
        msg.body = f"""
        Hola {cita.paciente.nombre_completo},
        
        Lamentamos informarte que tu cita programada para el {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')} 
        con {cita.psicologo.nombre_completo} ha sido rechazada.
        
        Por favor, contacta a la clínica para más información.
        
        Saludos,
        Equipo Clínica Mentalmente
        """
        
        mail.send(msg)
        logger.info(f"Correo de rechazo enviado a {cita.paciente.email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de rechazo: {str(e)}")
        flash('Error al enviar correo de rechazo', 'error')
        return False

def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def enviar_correo_firma(cita):
    try:
        # Si el paciente tiene tutor, enviar al tutor, si no al paciente
        if hasattr(cita.paciente, 'tutor') and cita.paciente.tutor:
            recipients = [cita.paciente.tutor.email]
        else:
            recipients = [cita.paciente.email]
        msg = Message(
            "Firma de Consentimiento - Clínica Mentalmente",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=recipients
        )
        link_firma = url_for('firmar_consentimiento', token=cita.token_firma, _external=True)
        msg.html = f"""
        <h3>Hola {cita.paciente.nombre_completo},</h3>
        <p>Tu cita con {cita.psicologo.nombre_completo} ha sido confirmada para el {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}.</p>
        <p>Por favor firma el consentimiento informado en el siguiente enlace:</p>
        <a href=\"{link_firma}\">Firmar Consentimiento</a>
        <p>Saludos,<br>Equipo Clínica Mentalmente</p>
        """
        mail.send(msg)
        logger.info(f"Correo de firma enviado a {recipients}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de firma: {str(e)}")
        print(f"[ERROR ENVÍO CORREO FIRMA] {str(e)}")
        flash(f'La cita fue aceptada, pero hubo un problema al enviar el correo al paciente. Error SMTP: {str(e)}', 'danger')
        return False

def generar_pdf_paciente(cita, firma_paciente):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(25, 25, 25)
    
    pdf.ln(25) # Espacio para el header
    
    # Título
    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 5, "AUTORIZAR PROCESO PSICOLÓGICO E INFORMACIÓN A TERCEROS", 0, 'C')
    pdf.ln(15)
    
    # Texto principal con formato
    pdf.set_font("Arial", '', 11)
    
    # Párrafo 1
    pdf.write(5, "Yo ")
    pdf.set_font('', 'B')
    pdf.write(5, f"{cita.paciente.nombre_completo}")
    pdf.set_font('', '')
    pdf.write(5, " identificado(a) con documento de identidad Nº ")
    pdf.set_font('', 'B')
    pdf.write(5, f"{cita.paciente.numero_identificacion}")
    pdf.set_font('', '')
    pdf.write(5, f" de {cita.paciente.ciudad}")
    pdf.write(5, ", en pleno uso de mis facultades legales y mentales, de manera consciente y sin ninguna clase de presión, faculto y autorizo al profesional en psicología ")
    pdf.set_font('', 'B')
    pdf.write(5, f"{cita.psicologo.nombre_completo}")
    pdf.set_font('', '')
    pdf.write(5, ", para que realice proceso de evaluación, diagnóstico, pronóstico, tratamiento, asesoría y orientación psicológica. Igualmente advierto que se me ha puesto en conocimiento, y acepto las terapias y procedimientos que el terapeuta considere son las adecuadas para mi condición psicológica o la del niño que represento.")
    pdf.ln(10)

    # Párrafos siguientes
    texto_largo = """También se me ha ilustrado de manera clara y precisa, sobre: Rol del terapeuta, sus cualificaciones y alcances profesionales, los procedimientos terapéuticos y sus propósitos, las incomodidades o riesgos potenciales que se pueden derivar del proceso, los beneficios razonables que se pueden esperar acorde a mi participación, asistencia y compromiso con el proceso sean los indicados, alternativas posibles a la terapia dentro de la disciplina científica y los recursos del medio para brindarme apoyo, que puedo retirarme del proceso en cualquier momento, los límites de la confidencialidad y manejo de información de datos según disposiciones de ley.

Además, se me informo así mismo, que al venir a proceso psicológico estoy aceptando un servicio para el cual debo suministrar la información necesaria para obtener beneficios del proceso, lo relacionado con el funcionamiento del proceso psicológico, las posibilidades de mejoramiento, la duración del tratamiento y la aplicación de técnicas y pruebas psicológicas pertinentes.

- También se me explicó lo concerniente a la forma de pago y circunstancias relacionadas con el incumplimiento de las citas o deserción por parte mía o del terapeuta.

- Que la confidencialidad de la profesión de psicología está regida por el artículo 2o, numeral 5o de la Ley 1090 de 2006: "Los psicólogos que ejerzan su profesión en Colombia se regirán por los siguientes principios universales: 5. Confidencialidad. Los psicólogos tienen una obligación básica respecto a la confidencialidad de la información obtenida de las personas en el desarrollo de su trabajo como psicólogos. Revelarán tal información a los demás solo con el consentimiento de la persona o del representante legal de la persona, excepto en aquellas circunstancias particulares en que no hacerlo llevaría a un evidente daño a la persona o a otros. Los psicólogos informarán a sus usuarios de las limitaciones legales de la confidencialidad".

Autorizo con la firma de este documento que mi historia clínica sea suministrada a terceros en caso de que sea requerida para fines terapéuticos y/o jurídicos, según las disposiciones de ley."""
    pdf.multi_cell(0, 5, texto_largo, align='J')
    pdf.ln(10)
    
    # Sección de manejo de datos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "MANEJO DE DATOS PERSONALES", ln=1, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 11)
    
    texto_datos_1 = "Declaro de manera libre, expresa, inequívoca e informada, que AUTORIZO a él profesional en psicología "
    pdf.write(5, texto_datos_1)
    pdf.set_font('', 'B')
    pdf.write(5, f"{cita.psicologo.nombre_completo}")
    pdf.set_font('', '')

    texto_datos_2 = """ para que, en los términos del literal a) del artículo 6 de la Ley 1581 de 2012, realice la recolección, almacenamiento, uso, circulación, supresión, y en general, tratamiento de mis datos personales, incluyendo datos sensibles, como la historia clínica y demás datos que puedan llegar a ser considerados como sensibles de conformidad con la Ley, para que dicho Tratamiento se realice con el fin de lograr las finalidades relativas a ejecutar el control, seguimiento, monitoreo, vigilancia y, en general, garantizar la seguridad de sus instalaciones; así como para documentar las actividades gremiales.

Declaro que se me ha informado de manera clara y comprensible que tengo derecho a conocer, actualizar y rectificar los datos personales proporcionados, a solicitar prueba de esta autorización, a solicitar información sobre el uso que se le ha dado a mis datos personales, a presentar quejas ante la Superintendencia de Industria y comercio por el uso indebido de mis datos personales, a revocar esta autorización o solicitar la supresión de los datos personales suministrados y a acceder de forma gratuita a los mismos.

Declaro que conozco y acepto el manual de tratamiento de datos personales de MentalMente Psicología Especializada y que la información por mí proporcionada es veraz, completa, exacta, actualizada y verificable. Mediante la firma del presente documento, manifiesto que reconozco y acepto que cualquier consulta o reclamación relacionada con el tratamiento de mis datos personales"""
    pdf.ln()
    pdf.multi_cell(0, 5, texto_datos_2, align='J')
    pdf.ln(5)
    
    # Fecha y firma
    meses = {"January": "enero", "February": "febrero", "March": "marzo", "April": "abril", "May": "mayo", "June": "junio", "July": "julio", "August": "agosto", "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"}
    fecha_actual = datetime.now()
    nombre_mes_ingles = fecha_actual.strftime('%B')
    nombre_mes = meses.get(nombre_mes_ingles, nombre_mes_ingles)

    pdf.write(5, "Acepto las condiciones que se me presentan en este documento, dado en ")
    pdf.set_font('', 'B')
    pdf.write(5, f"{cita.paciente.ciudad}")
    pdf.set_font('', '')
    pdf.write(5, f", el día {fecha_actual.strftime('%d')} del mes de {nombre_mes} del año {fecha_actual.strftime('%Y')}")
    pdf.ln(8)
    pdf.cell(0, 5, "Para constancia se firma la conformidad.", ln=1)
    
    # Tabla de firmas
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    
    col_width_name = 80
    col_width_firma = 50
    col_width_fecha = 30
    
    pdf.cell(col_width_name, 8, "Nombres y apellidos del paciente*", border=1)
    pdf.cell(col_width_firma, 8, "Firma", border=1)
    pdf.cell(col_width_fecha, 8, "Fecha", border=1, ln=1)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(col_width_name, 20, f"{cita.paciente.nombre_completo}", border=1)
    
    firma_path = f"static/firmas/firma_{cita.id}.png"
    with open(firma_path, "wb") as f:
        f.write(base64.b64decode(re.sub('^data:image/.+;base64,', '', firma_paciente)))
    x, y = pdf.get_x(), pdf.get_y()
    pdf.cell(col_width_firma, 20, "", border=1)
    pdf.image(firma_path, x=x+2.5, y=y+2, w=45, h=16)
    pdf.set_font("Arial", '', 11)
    pdf.cell(col_width_fecha, 20, f"{fecha_actual.strftime('%Y-%m-%d')}", border=1, ln=1, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(col_width_name, 8, f"C.C: {cita.paciente.numero_identificacion}", border=1)
    pdf.cell(col_width_firma, 8, "", border=1)
    pdf.cell(col_width_fecha, 8, "", border=1, ln=1)
    pdf.ln(10)

    # Si existe tutor, agregar fila de responsable
    if hasattr(cita.paciente, 'tutor') and cita.paciente.tutor:
        tutor = cita.paciente.tutor
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 8, "Nombres y apellidos del Responsable del Paciente", border=1)
        pdf.cell(col_width_firma, 8, "Ciudad", border=1)
        pdf.cell(col_width_fecha, 8, "Fecha", border=1, ln=1)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 20, f"{tutor.nombre_completo}", border=1)
        pdf.cell(col_width_firma, 20, f"{tutor.ciudad}", border=1)
        pdf.cell(col_width_fecha, 20, f"{fecha_actual.strftime('%Y-%m-%d')}", border=1, ln=1)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 8, f"C.C: {tutor.numero_identificacion}", border=1)
        pdf.cell(col_width_firma, 8, "", border=1)
        pdf.cell(col_width_fecha, 8, "", border=1, ln=1)
        pdf.ln(10)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(col_width_name, 8, "Profesional", border=1)
    pdf.cell(col_width_firma, 8, "Firma", border=1)
    pdf.cell(col_width_fecha, 8, "Fecha", border=1, ln=1)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(col_width_name, 20, f"{cita.psicologo.nombre_completo}", border=1)
    pdf.cell(col_width_firma, 20, "", border=1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(col_width_fecha, 20, "", border=1, ln=1)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(col_width_name, 8, f"C.C: {getattr(cita.psicologo, 'numero_identificacion', '')}", border=1)
    pdf.cell(col_width_firma, 8, "", border=1)
    pdf.cell(col_width_fecha, 8, "", border=1, ln=1)
    
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    pdf_path = f"pdfs/consentimiento_{cita.id}.pdf"
    pdf.output(pdf_path)
    return pdf_path

def generar_pdf_final(consentimiento, firma_psicologo):
    try:
        pdf = PDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(25, 25, 25)
        
        pdf.ln(25)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 5, "AUTORIZAR PROCESO PSICOLÓGICO E INFORMACIÓN A TERCEROS", 0, 'C')
        pdf.ln(15)
        
        pdf.set_font("Arial", '', 11)
        
        pdf.write(5, "Yo ")
        pdf.set_font('', 'B')
        pdf.write(5, f"{consentimiento.cita.paciente.nombre_completo}")
        pdf.set_font('', '')
        pdf.write(5, " identificado(a) con documento de identidad Nº ")
        pdf.set_font('', 'B')
        pdf.write(5, f"{consentimiento.cita.paciente.numero_identificacion}")
        pdf.set_font('', '')
        ciudad = getattr(consentimiento.cita.psicologo, 'ciudad', '')
        if ciudad:
            pdf.write(5, f" de {ciudad}")
        
        pdf.write(5, ", en pleno uso de mis facultades legales y mentales, de manera consciente y sin ninguna clase de presión, faculto y autorizo al profesional en psicología ")
        pdf.set_font('', 'B')
        pdf.write(5, f"{consentimiento.cita.psicologo.nombre_completo}")
        pdf.set_font('', '')
        pdf.write(5, ", para que realice proceso de evaluación, diagnóstico, pronóstico, tratamiento, asesoría y orientación psicológica. Igualmente advierto que se me ha puesto en conocimiento, y acepto las terapias y procedimientos que el terapeuta considere son las adecuadas para mi condición psicológica o la del niño que represento.")
        pdf.ln(10)

        texto_largo = """También se me ha ilustrado de manera clara y precisa, sobre: Rol del terapeuta, sus cualificaciones y alcances profesionales, los procedimientos terapéuticos y sus propósitos, las incomodidades o riesgos potenciales que se pueden derivar del proceso, los beneficios razonables que se pueden esperar acorde a mi participación, asistencia y compromiso con el proceso sean los indicados, alternativas posibles a la terapia dentro de la disciplina científica y los recursos del medio para brindarme apoyo, que puedo retirarme del proceso en cualquier momento, los límites de la confidencialidad y manejo de información de datos según disposiciones de ley.

Además, se me informo así mismo, que al venir a proceso psicológico estoy aceptando un servicio para el cual debo suministrar la información necesaria para obtener beneficios del proceso, lo relacionado con el funcionamiento del proceso psicológico, las posibilidades de mejoramiento, la duración del tratamiento y la aplicación de técnicas y pruebas psicológicas pertinentes.

- También se me explicó lo concerniente a la forma de pago y circunstancias relacionadas con el incumplimiento de las citas o deserción por parte mía o del terapeuta.

- Que la confidencialidad de la profesión de psicología está regida por el artículo 2o, numeral 5o de la Ley 1090 de 2006: "Los psicólogos que ejerzan su profesión en Colombia se regirán por los siguientes principios universales: 5. Confidencialidad. Los psicólogos tienen una obligación básica respecto a la confidencialidad de la información obtenida de las personas en el desarrollo de su trabajo como psicólogos. Revelarán tal información a los demás solo con el consentimiento de la persona o del representante legal de la persona, excepto en aquellas circunstancias particulares en que no hacerlo llevaría a un evidente daño a la persona o a otros. Los psicólogos informarán a sus usuarios de las limitaciones legales de la confidencialidad".

Autorizo con la firma de este documento que mi historia clínica sea suministrada a terceros en caso de que sea requerida para fines terapéuticos y/o jurídicos, según las disposiciones de ley."""
        pdf.multi_cell(0, 5, texto_largo, align='J')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "MANEJO DE DATOS PERSONALES", ln=1, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", '', 11)
        
        texto_datos_1 = "Declaro de manera libre, expresa, inequívoca e informada, que AUTORIZO a él profesional en psicología "
        pdf.write(5, texto_datos_1)
        pdf.set_font('', 'B')
        pdf.write(5, f"{consentimiento.cita.psicologo.nombre_completo}")
        pdf.set_font('', '')
        
        texto_datos_2 = """ para que, en los términos del literal a) del artículo 6 de la Ley 1581 de 2012, realice la recolección, almacenamiento, uso, circulación, supresión, y en general, tratamiento de mis datos personales, incluyendo datos sensibles, como la historia clínica y demás datos que puedan llegar a ser considerados como sensibles de conformidad con la Ley, para que dicho Tratamiento se realice con el fin de lograr las finalidades relativas a ejecutar el control, seguimiento, monitoreo, vigilancia y, en general, garantizar la seguridad de sus instalaciones; así como para documentar las actividades gremiales.

Declaro que se me ha informado de manera clara y comprensible que tengo derecho a conocer, actualizar y rectificar los datos personales proporcionados, a solicitar prueba de esta autorización, a solicitar información sobre el uso que se le ha dado a mis datos personales, a presentar quejas ante la Superintendencia de Industria y comercio por el uso indebido de mis datos personales, a revocar esta autorización o solicitar la supresión de los datos personales suministrados y a acceder de forma gratuita a los mismos.

Declaro que conozco y acepto el manual de tratamiento de datos personales de MentalMente Psicología Especializada y que la información por mí proporcionada es veraz, completa, exacta, actualizada y verificable. Mediante la firma del presente documento, manifiesto que reconozco y acepto que cualquier consulta o reclamación relacionada con el tratamiento de mis datos personales"""
        pdf.ln()
        pdf.multi_cell(0, 5, texto_datos_2, align='J')
        pdf.ln(5)
        
        meses = {"January": "enero", "February": "febrero", "March": "marzo", "April": "abril", "May": "mayo", "June": "junio", "July": "julio", "August": "agosto", "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"}
        fecha_actual = datetime.now()
        nombre_mes_ingles = fecha_actual.strftime('%B')
        nombre_mes = meses.get(nombre_mes_ingles, nombre_mes_ingles)
        
        pdf.write(5, "Acepto las condiciones que se me presentan en este documento, dado en ")
        ciudad = getattr(consentimiento.cita.psicologo, 'ciudad', '')
        if ciudad:
            pdf.set_font('', 'B')
            pdf.write(5, f"{ciudad}")
            pdf.set_font('', '')
        else:
            pdf.write(5, "__________")
        pdf.write(5, f", el día {fecha_actual.strftime('%d')} del mes de {nombre_mes} del año {fecha_actual.strftime('%Y')}")

        pdf.ln(8)
        pdf.cell(0, 5, "Para constancia se firma la conformidad.", ln=1)
        
        # Tabla de firmas
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 11)
        
        col_width_name = 80
        col_width_firma = 50
        col_width_fecha = 30

        pdf.cell(col_width_name, 8, "Nombres y apellidos del paciente*", border=1)
        pdf.cell(col_width_firma, 8, "Firma", border=1)
        pdf.cell(col_width_fecha, 8, "Fecha", border=1, ln=1)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 20, f"{consentimiento.cita.paciente.nombre_completo}", border=1)
        
        firma_paciente_path = f"static/firmas/firma_{consentimiento.cita.id}.png"
        x, y = pdf.get_x(), pdf.get_y()
        pdf.cell(col_width_firma, 20, "", border=1)
        pdf.image(firma_paciente_path, x=x+2.5, y=y+2, w=45, h=16)
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(col_width_fecha, 20, f"{consentimiento.fecha_firma_paciente.strftime('%Y-%m-%d')}", border=1, ln=1, align='C')
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 8, f"C.C: {consentimiento.cita.paciente.numero_identificacion}", border=1)
        pdf.cell(col_width_firma, 8, "", border=1)
        pdf.cell(col_width_fecha, 8, "", border=1, ln=1)
        
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 8, "Profesional", border=1)
        pdf.cell(col_width_firma, 8, "Firma", border=1)
        pdf.cell(col_width_fecha, 8, "Fecha", border=1, ln=1)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 20, f"{consentimiento.cita.psicologo.nombre_completo}", border=1)
        
        firma_psicologo_path = f"static/firmas/firma_psicologo_{consentimiento.cita.id}.png"
        with open(firma_psicologo_path, "wb") as f:
            f.write(base64.b64decode(re.sub('^data:image/.+;base64,', '', firma_psicologo)))
        x, y = pdf.get_x(), pdf.get_y()
        pdf.cell(col_width_firma, 20, "", border=1)
        pdf.image(firma_psicologo_path, x=x+2.5, y=y+2, w=45, h=16)

        pdf.set_font("Arial", '', 11)
        pdf.cell(col_width_fecha, 20, f"{datetime.now().strftime('%Y-%m-%d')}", border=1, ln=1, align='C')
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width_name, 8, f"C.C: {getattr(consentimiento.cita.psicologo, 'numero_identificacion', '')}", border=1)
        pdf.cell(col_width_firma, 8, "", border=1)
        pdf.cell(col_width_fecha, 8, "", border=1, ln=1)
        
        pdf_path = f"pdfs/consentimiento_final_{consentimiento.cita.id}.pdf"
        pdf.output(pdf_path)
        
        return pdf_path
    except Exception as e:
        logger.error(f"Error al generar PDF final: {str(e)}")
        raise

def enviar_copia_final(cita, pdf_path):
    try:
        msg = Message(
            "Consentimiento firmado - Clínica Mentalmente",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[cita.paciente.email]  # Solo al paciente
        )
        
        msg.html = f"""
        <h3>Hola {cita.paciente.nombre_completo},</h3>
        <p>Adjunto encontrará el consentimiento informado firmado por ambas partes para su cita del {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}.</p>
        <p>Saludos,<br>Equipo Clínica Mentalmente</p>
        """
        
        with open(pdf_path, 'rb') as f:
            msg.attach("consentimiento_firmado.pdf", "application/pdf", f.read())
        
        mail.send(msg)
        logger.info(f"Copia final enviada a {cita.paciente.email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar copia final: {str(e)}")
        flash('Error al enviar copia del documento firmado', 'error')
        return False

# --- Rutas ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendar', methods=['GET', 'POST'])
def agendar_cita():
    if request.method == 'POST':
        try:
            # 1. Extraer y validar datos del formulario
            psicologo_id_str = request.form.get('psicologo_id')
            fecha_hora_str = request.form.get('fecha_hora')
            nombre_completo = request.form.get('nombre_completo')
            tipo_identificacion = request.form.get('tipo_identificacion')
            numero_identificacion = request.form.get('numero_identificacion')
            email = request.form.get('email')
            telefono = request.form.get('telefono')
            fecha_nacimiento_str = request.form.get('fecha_nacimiento')
            genero = request.form.get('genero')
            direccion = request.form.get('direccion')
            ciudad = request.form.get('ciudad')

            # Validar que todos los campos necesarios están presentes y no son solo espacios en blanco
            required_fields = {
                'ID del Psicólogo': psicologo_id_str,
                'Fecha y Hora': fecha_hora_str,
                'Nombre Completo': nombre_completo,
                'Tipo de Identificación': tipo_identificacion,
                'Número de Identificación': numero_identificacion,
                'Email': email,
                'Teléfono': telefono,
                'Fecha de Nacimiento': fecha_nacimiento_str,
                'Género': genero,
                'Dirección': direccion,
                'Ciudad': ciudad
            }

            for field_name, value in required_fields.items():
                if not value or not value.strip():
                    flash(f'El campo "{field_name}" es obligatorio.', 'danger')
                    return redirect(url_for('agendar_cita'))

            # Aseguramos a mypy que los valores no son None
            assert psicologo_id_str is not None
            assert fecha_hora_str is not None
            assert nombre_completo is not None
            assert tipo_identificacion is not None
            assert numero_identificacion is not None
            assert email is not None
            assert telefono is not None
            assert fecha_nacimiento_str is not None
            assert genero is not None
            assert direccion is not None
            assert ciudad is not None

            # Convertir strings a los tipos de datos correctos
            psicologo_id = int(psicologo_id_str)
            fecha_hora = datetime.fromisoformat(fecha_hora_str)
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()

            # 2. Buscar o crear el paciente
            paciente = Paciente.query.filter_by(numero_identificacion=numero_identificacion).first()

            if not paciente:
                # Si el paciente no existe, lo creamos
                paciente = Paciente(
                    nombre_completo=nombre_completo,
                    tipo_identificacion=tipo_identificacion,
                    numero_identificacion=numero_identificacion,
                    email=email,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nacimiento,
                    genero=genero,
                    direccion=direccion,
                    ciudad=ciudad
                )
                db.session.add(paciente)
                db.session.flush()
            else:
                # Si el paciente ya existe, actualizamos sus datos
                paciente.nombre_completo = nombre_completo
                paciente.email = email
                paciente.telefono = telefono
                paciente.fecha_nacimiento = fecha_nacimiento
                paciente.genero = genero
                paciente.direccion = direccion
                paciente.ciudad = ciudad

            # Calcular edad y determinar si requiere tutor
            edad = calcular_edad(fecha_nacimiento)
            requiere_tutor = edad < 18 or tipo_identificacion in ["TI", "RC"]
            tutor = None
            if requiere_tutor:
                tutor_nombre_completo = request.form.get('tutor_nombre_completo')
                tutor_tipo_identificacion = request.form.get('tutor_tipo_identificacion')
                tutor_numero_identificacion = request.form.get('tutor_numero_identificacion')
                tutor_email = request.form.get('tutor_email')
                tutor_telefono = request.form.get('tutor_telefono')
                tutor_ciudad = request.form.get('tutor_ciudad')
                if not all([tutor_nombre_completo, tutor_tipo_identificacion, tutor_numero_identificacion, tutor_email, tutor_telefono, tutor_ciudad]):
                    flash('Todos los campos del tutor son obligatorios para menores de edad.', 'danger')
                    return redirect(url_for('agendar_cita'))
                if hasattr(paciente, 'tutor') and paciente.tutor:
                    tutor = paciente.tutor
                    tutor.nombre_completo = tutor_nombre_completo
                    tutor.tipo_identificacion = tutor_tipo_identificacion
                    tutor.numero_identificacion = tutor_numero_identificacion
                    tutor.email = tutor_email
                    tutor.telefono = tutor_telefono
                    tutor.ciudad = tutor_ciudad
                else:
                    tutor = Tutor(
                        nombre_completo=tutor_nombre_completo,
                        tipo_identificacion=tutor_tipo_identificacion,
                        numero_identificacion=tutor_numero_identificacion,
                        email=tutor_email,
                        telefono=tutor_telefono,
                        ciudad=tutor_ciudad,
                        paciente_id=paciente.id
                    )
                    db.session.add(tutor)
                email_destino = tutor_email
            else:
                email_destino = email

            # 3. Crear la nueva cita
            token_firma = secrets.token_urlsafe(32)
            print(f"[DEBUG] Token generado para la cita: {token_firma}")
            nueva_cita = Cita(
                paciente_id=paciente.id,
                psicologo_id=psicologo_id,
                fecha_hora=fecha_hora,
                duracion_minutos=45,
                tipo_consulta='primera_vez',
                estado='pendiente',
                token_firma=token_firma
            )
            db.session.add(nueva_cita)
            print(f"[DEBUG] Antes de commit: Cita ID: {getattr(nueva_cita, 'id', None)}, Token: {nueva_cita.token_firma}")
            db.session.commit()
            print(f"[DEBUG] Después de commit: Cita ID: {nueva_cita.id}, Token: {nueva_cita.token_firma}")
            flash('¡Cita agendada exitosamente! Se ha enviado un correo de confirmación.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # Revertir cambios en caso de error
            app.logger.error(f"Error al agendar la cita: {e}\nForm Data: {request.form.to_dict()}")
            flash('Danger! Error al agendar la cita. Por favor intenta nuevamente.', 'danger')
            return redirect(url_for('agendar_cita'))

    # Método GET
    psicologos = Psicologo.query.all()
    return render_template('agendar.html', psicologos=psicologos)

@app.route('/admin/citas')
def admin_citas():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    citas_pendientes: List[Cita] = Cita.query.filter_by(estado='pendiente').order_by(Cita.fecha_hora.asc()).all()  # type: ignore
    return render_template('admin/citas.html', citas=citas_pendientes)

@app.route('/admin/decision_cita/<int:cita_id>', methods=['POST'])
def decision_cita(cita_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    cita = Cita.query.get_or_404(cita_id)
    decision = request.form['decision']
    
    try:
        if decision == 'aceptar':
            cita.estado = 'aceptada'
            if not enviar_correo_firma(cita):
                flash('La cita fue aceptada pero hubo un error al enviar el correo', 'warning')
        else:
            cita.estado = 'rechazada'
            if not enviar_correo_rechazo(cita):
                flash('La cita fue rechazada pero hubo un error al enviar el correo', 'warning')
        
        db.session.commit()
        flash(f'Cita {decision} correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en decisión de cita: {str(e)}")
        flash('Error al procesar la decisión', 'danger')
    
    return redirect(url_for('admin_citas'))

@app.route('/firmar/<token>', methods=['GET', 'POST'])
def firmar_consentimiento(token):
    cita = Cita.query.filter_by(token_firma=token).first_or_404()
    
    if request.method == 'POST':
        if 'firma_paciente' not in request.form:
            flash('Debes proporcionar una firma', 'danger')
            return redirect(url_for('firmar_consentimiento', token=token))
        
        try:
            firma_paciente = request.form['firma_paciente']
            pdf_path = generar_pdf_paciente(cita, firma_paciente)
            
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            nuevo_consentimiento = Consentimiento(
                cita_id=cita.id,
                firma_paciente=firma_paciente,
                ip_paciente=request.remote_addr,
                dispositivo_paciente=request.user_agent.string,
                fecha_firma_paciente=datetime.now(),
                pdf_final=pdf_data
            )
            
            db.session.add(nuevo_consentimiento)
            cita.estado = 'firmado_paciente'
            db.session.commit()
            
            flash('Consentimiento firmado correctamente. El psicólogo lo revisará.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al firmar consentimiento: {str(e)}")
            flash('Error al procesar tu firma. Por favor intenta nuevamente.', 'danger')
            return redirect(url_for('firmar_consentimiento', token=token))
    
    return render_template('firma_paciente.html', cita=cita, fecha_actual=datetime.now())

@app.route('/psicologo/firmar/<int:cita_id>', methods=['GET', 'POST'])
def firma_psicologo(cita_id):
    if 'psicologo_id' not in session:
        return redirect(url_for('login_psicologo'))
    
    consentimiento = Consentimiento.query.filter_by(cita_id=cita_id).first_or_404()
    
    if request.method == 'POST':
        if 'firma_psicologo' not in request.form:
            flash('Debes proporcionar una firma', 'danger')
            return redirect(url_for('firma_psicologo', cita_id=cita_id))
        
        try:
            firma_psicologo = request.form['firma_psicologo']
            pdf_final = generar_pdf_final(consentimiento, firma_psicologo)
            
            with open(pdf_final, 'rb') as f:
                pdf_data = f.read()
            
            consentimiento.firma_psicologo = firma_psicologo
            consentimiento.pdf_final = pdf_data
            consentimiento.fecha_firma_psicologo = datetime.now()
            
            cita = Cita.query.get(cita_id)
            if cita is None:
                flash('No se encontró la cita.', 'danger')
                return redirect(url_for('panel_psicologo'))
            
            cita.estado = 'completada'
            db.session.commit()
            
            if not enviar_copia_final(cita, pdf_final):
                flash('Consentimiento completado, pero hubo un error al enviar el correo', 'warning')
            else:
                flash('Consentimiento completado y enviado al paciente.', 'success')
            return redirect(url_for('panel_psicologo'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al firmar como psicólogo: {str(e)}")
            flash('Error al procesar tu firma. Por favor intenta nuevamente.', 'danger')
            return redirect(url_for('firma_psicologo', cita_id=cita_id))
    
    return render_template('psicologo/firma.html', consentimiento=consentimiento)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    citas_pendientes: int = Cita.query.filter_by(estado='pendiente').count()
    citas_aceptadas: int = Cita.query.filter_by(estado='aceptada').count()
    citas_completadas: int = Cita.query.filter_by(estado='completada').count()
    ultimas_citas: List[Cita] = Cita.query.order_by(Cita.fecha_hora.desc()).limit(10).all()  # type: ignore

    return render_template(
        'admin/dashboard.html',
        citas_pendientes=citas_pendientes,
        citas_aceptadas=citas_aceptadas,
        citas_completadas=citas_completadas,
        ultimas_citas=ultimas_citas
    )

@app.route('/admin/usuarios')
def admin_usuarios():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    usuarios = []  # Aquí deberías cargar los usuarios desde la base de datos
    return render_template('admin/usuarios.html', usuarios=usuarios)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        if usuario == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Inicio de sesión de administrador exitoso', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('admin/login.html')

@app.route('/logout')
def logout():
    is_admin = session.pop('admin_logged_in', None)
    is_psicologo = session.pop('psicologo_id', None)
    session.pop('user_email', None)
    flash('Sesión cerrada correctamente', 'success')
    if is_admin:
        return redirect(url_for('admin_login'))
    elif is_psicologo:
        return redirect(url_for('login_psicologo'))
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin/cita/<int:cita_id>')
def ver_cita(cita_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    cita = Cita.query.get_or_404(cita_id)
    return render_template('admin/ver_cita.html', cita=cita)

@app.route('/test_mail')
def test_mail():
    try:
        msg = Message(
            "Prueba de correo - Clínica Mentalmente",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=["citasmentalmente@gmail.com"]
        )
        msg.body = "Esto es una prueba de envío de correo desde Flask-Mail."
        mail.send(msg)
        return "Correo enviado correctamente. Revisa la bandeja de entrada y spam."
    except Exception as e:
        return f"Error al enviar correo: {str(e)}"

@app.route('/admin/reenviar_correo_cita/<int:cita_id>', methods=['POST'])
def reenviar_correo_cita(cita_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    cita = Cita.query.get_or_404(cita_id)
    if enviar_correo_firma(cita):
        flash('Correo de firma reenviado al paciente.', 'success')
    else:
        flash('Error al reenviar el correo de firma', 'danger')
    return redirect(url_for('admin_citas'))

@app.route('/psicologo/login', methods=['GET', 'POST'])
def login_psicologo():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email, tipo='psicologo', activo=True).first()
        
        if usuario and usuario.password_hash == password:  # En producción usar hash
            psicologo = usuario.psicologo
            if psicologo:
                session['psicologo_id'] = psicologo.id
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('panel_psicologo'))
            else:
                flash('Error: Usuario no asociado a un psicólogo', 'danger')
        else:
            flash('Credenciales incorrectas', 'danger')
    
    return render_template('psicologo/login.html')

@app.route('/psicologo/panel')
def panel_psicologo():
    if 'psicologo_id' not in session:
        return redirect(url_for('login_psicologo'))
    
    psicologo_id: int = session['psicologo_id']
    psicologo: Psicologo = Psicologo.query.get_or_404(psicologo_id)
    
    # Obtener citas aceptadas (paciente aún no ha firmado)
    citas_aceptadas: List[Cita] = db.session.query(Cita).join(
        Paciente, Cita.paciente_id == Paciente.id
    ).filter(
        Cita.psicologo_id == psicologo_id,  # type: ignore
        Cita.estado == 'aceptada'  # type: ignore
    ).order_by(Cita.fecha_hora.desc()).all()  # type: ignore
    
    # Obtener consentimientos pendientes de firma del psicólogo
    # Buscar citas que tienen consentimiento pero el psicólogo aún no ha firmado
    citas_pendientes_firma: Sequence[Any] = db.session.query(
        Cita, Paciente, Consentimiento
    ).join(
        Paciente, Cita.paciente_id == Paciente.id
    ).join(
        Consentimiento, Cita.id == Consentimiento.cita_id
    ).filter(
        Cita.psicologo_id == psicologo_id,  # type: ignore
        Consentimiento.firma_psicologo.is_(None)  # type: ignore
    ).order_by(Cita.fecha_hora.desc()).all()  # type: ignore
    
    # Obtener consentimientos ya firmados (completados)
    citas_firmadas: Sequence[Any] = db.session.query(
        Cita, Paciente, Consentimiento
    ).join(
        Paciente, Cita.paciente_id == Paciente.id
    ).join(
        Consentimiento, Cita.id == Consentimiento.cita_id
    ).filter(
        Cita.psicologo_id == psicologo_id,  # type: ignore
        Consentimiento.firma_psicologo.isnot(None)  # type: ignore
    ).order_by(Cita.fecha_hora.desc()).all()  # type: ignore
    
    return render_template('psicologo/panel.html', 
                         psicologo=psicologo,
                         citas_aceptadas=citas_aceptadas,
                         citas_pendientes_firma=citas_pendientes_firma,
                         citas_firmadas=citas_firmadas)

@app.route('/psicologo/ver_consentimiento/<int:cita_id>')
def ver_consentimiento(cita_id):
    if 'psicologo_id' not in session:
        return redirect(url_for('login_psicologo'))
    
    psicologo_id = session['psicologo_id']
    cita = Cita.query.filter_by(id=cita_id, psicologo_id=psicologo_id).first_or_404()
    consentimiento = Consentimiento.query.filter_by(cita_id=cita_id).first_or_404()
    
    # Generar una URL temporal para ver el PDF
    pdf_path = f"pdfs/consentimiento_{cita.id}.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=False)
    else:
        flash('El archivo PDF no está disponible', 'danger')
        return redirect(url_for('panel_psicologo'))

@app.route('/psicologo/descargar_consentimiento/<int:cita_id>')
def descargar_consentimiento(cita_id):
    if 'psicologo_id' not in session:
        return redirect(url_for('login_psicologo'))
    
    psicologo_id = session['psicologo_id']
    cita = Cita.query.filter_by(id=cita_id, psicologo_id=psicologo_id).first_or_404()
    consentimiento = Consentimiento.query.filter_by(cita_id=cita_id).first_or_404()
    
    if cita.estado == 'completada':
        pdf_path = f"pdfs/consentimiento_final_{cita.id}.pdf"
    else:
        pdf_path = f"pdfs/consentimiento_{cita.id}.pdf"
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, 
                        as_attachment=True,
                        download_name=f"consentimiento_{cita.paciente.nombre_completo}.pdf")
    else:
        flash('El archivo PDF no está disponible', 'danger')
        return redirect(url_for('panel_psicologo'))

# --- Endpoint para obtener horarios disponibles ---
@app.route('/get-available-times')
def get_available_times():
    psychologist_id_str = request.args.get('psicologo_id')
    date_str = request.args.get('date')
    
    if not psychologist_id_str or not date_str:
        return jsonify({'error': 'Faltan parámetros'}), 400

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        psychologist_id = int(psychologist_id_str)
    except (ValueError, TypeError):
        return jsonify({'error': 'Formato de fecha o ID inválido'}), 400

    # Horario laboral estándar (de 8 AM a 5 PM)
    work_start_hour = 8
    work_end_hour = 17
    all_slots = [f"{hour:02d}:00" for hour in range(work_start_hour, work_end_hour)]

    # Obtener citas ya agendadas para ese día y psicólogo
    booked_appointments = db.session.query(Cita).filter_by(
        psicologo_id=psychologist_id
    ).filter(
        db.func.date(Cita.fecha_hora) == selected_date
    ).all()

    booked_times = {cita.fecha_hora.strftime('%H:%M') for cita in booked_appointments}

    # Filtrar para obtener solo los horarios disponibles
    available_slots = [slot for slot in all_slots if slot not in booked_times]

    return jsonify(available_slots)

@app.route('/get-psychologist-image/<int:psychologist_id>')
def get_psychologist_image(psychologist_id):
    # Implementa la lógica para obtener la imagen del psicólogo aquí
    # Esto es solo un ejemplo y debería ser reemplazado por la implementación real
    return "Imagen del psicólogo"

# --- Inicialización ---
with app.app_context():
    try:
        db.create_all()
        os.makedirs('pdfs', exist_ok=True)
        os.makedirs('static/firmas', exist_ok=True)
        
        # Actualizar automáticamente el estado de las citas existentes
        try:
            # Buscar citas con estado vacío que tienen consentimientos
            citas_con_consentimiento = db.session.query(Cita).join(
                Consentimiento, Cita.id == Consentimiento.cita_id
            ).filter_by(estado='').all()
            
            for cita in citas_con_consentimiento:
                consentimiento = Consentimiento.query.filter_by(cita_id=cita.id).first()
                if consentimiento:
                    if consentimiento.firma_psicologo:
                        cita.estado = 'completada'
                    else:
                        cita.estado = 'firmado_paciente'
            
            # Buscar citas con estado vacío que no tienen consentimientos
            citas_sin_consentimiento = db.session.query(Cita).filter_by(
                estado = ''
            ).all()
            
            for cita in citas_sin_consentimiento:
                consentimiento = Consentimiento.query.filter_by(cita_id=cita.id).first()
                if not consentimiento:
                    cita.estado = 'aceptada'
            
            db.session.commit()
            logger.info("Estados de citas actualizados correctamente")
        except Exception as e:
            logger.error(f"Error al actualizar estados de citas: {str(e)}")
            db.session.rollback()
        
        logger.info("Aplicación inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la aplicación: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
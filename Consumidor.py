import os.path
import base64
import pickle
import os
import google.auth
import google_auth_oauthlib.flow
import google.auth.transport.requests
import googleapiclient.discovery
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
import pika

# Configuración del cliente OAuth 2.0
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """
    Autentica el cliente de Gmail usando OAuth 2.0 y guarda el token de acceso en un archivo.
    """
    creds = None
    # Verifica si ya existe un token de acceso
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Si no existe el token o es inválido, solicita uno nuevo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Corre el servidor local en el puerto 8080 para la autenticación
            creds = flow.run_local_server(port=8080)
        # Guarda el token de acceso
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def send_email(creds, subject, body, destinatario):
    """
    Envía un correo electrónico usando la API de Gmail.

    Args:
    - creds: Credenciales de acceso de Google.
    - subject: Asunto del correo.
    - body: Cuerpo del correo.
    - destinatario: Dirección de correo del destinatario.
    """
    try:
        # Construye el servicio de la API de Gmail
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
        
        # Construye el mensaje del correo
        message = MIMEText(body)
        message['to'] = destinatario
        message['subject'] = subject
        
        # Codifica el mensaje en base64
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {'raw': raw}
        
        # Envía el mensaje usando la API de Gmail
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f" [x] Correo enviado a {destinatario}, ID del mensaje: {sent_message['id']}")
        
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

def callback(ch, method, properties, body):
    """
    Función de callback para procesar mensajes de la cola RabbitMQ.
    
    Args:
    - ch: Canal de comunicación.
    - method: Método de entrega.
    - properties: Propiedades del mensaje.
    - body: Cuerpo del mensaje.
    """
    print(f"[x] Recibido: {body.decode()}")
    send_email(authenticate_gmail(), 'Nuevo Mensaje de la Cola', body.decode(), 'emiliocabrera321@gmail.com')

def consume_message():
    """
    Conecta a RabbitMQ y consume mensajes de la cola.
    """
    # Conexión al servidor RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declaración de la cola
    channel.queue_declare(queue='test_queue')

    # Configuración del consumidor
    channel.basic_consume(queue='test_queue', on_message_callback=callback, auto_ack=True)

    print(' [*] Esperando mensajes. Para salir presione CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    # Inicia el consumo de mensajes de RabbitMQ
    consume_message()

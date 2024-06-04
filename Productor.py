import pika

def send_message(message):
    # Conexión al servidor RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declaración de la cola (debe ser la misma que en el consumidor)
    channel.queue_declare(queue='test_queue')

    # Envío del mensaje
    channel.basic_publish(exchange='',
                          routing_key='test_queue',
                          body=message)

    print(f" [x] Enviado '{message}'")
    connection.close()

if __name__ == "__main__":
    # Enviar un mensaje de prueba
    send_message('Hola, este es un mensaje de prueba.')


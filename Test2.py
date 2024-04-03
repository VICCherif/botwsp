import sqlite3
import pika
import ssl
import json

class MessageHandler:
    def __init__(self, db_file):
        self.db_file = db_file



    def insert_message(self, data):
        name = data.get("name", None)
        wp = data.get("wp", None)
        env = data.get("env", None)
        user_id = data.get("user_id", None)

        if name is not None and wp is not None and user_id is not None:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (name, wp, env, user_id, enviado)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, wp, env, user_id, 0))  # Use 0 as the default value for 'enviado'
                conn.commit()
        else:
            print("Error: Los datos recibidos no son válidos para la inserción.")



# Credenciales de RabbitMQ
username = "Admin"
password = "Factor.brucke*"
queue_name = "webhookQueueTest"

# Conexión al broker
connection_parameters = pika.ConnectionParameters(
    host="b-edd62bdc-e9f3-414d-82ea-b3e9261f5467.mq.us-west-2.amazonaws.com",
    port=5671,
    virtual_host="/",
    credentials=pika.PlainCredentials(username, password),
    ssl_options=pika.SSLOptions(context=ssl.create_default_context()),  # Use system CA certificates
)

try:
    connection = pika.BlockingConnection(connection_parameters)

    # Creación de un canal
    channel = connection.channel()

    message_handler = MessageHandler("stero.db")  # Aquí se pasa la ruta correcta de la base de datos

    # Función para consumir mensajes
    def on_message(channel, method, header, body):
        message = body.decode()
        print("Mensaje recibido:")
        print(message)
        # Parsear el mensaje JSON
        try:
            data = json.loads(message)
            message_handler.insert_message(data)
            print("Mensaje insertado en la base de datos.")
        except json.JSONDecodeError:
            print("Error al decodificar el mensaje JSON.")
        channel.basic_ack(delivery_tag=method.delivery_tag)

    # Iniciar consumo de la cola
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    # Esperar por mensajes
    print("Esperando por mensajes...")
    channel.start_consuming()

except pika.exceptions.ConnectionClosed as e:
    print("Connection error:", e)
    # Handle connection errors gracefully (e.g., retry logic)

finally:
    if connection:  # Check for connection within the 'try' block
        connection.close()
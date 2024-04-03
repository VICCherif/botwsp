import requests
import time
from PIL import Image
import sqlite3
import io
import os
import re
import time
from whatsapp_messenger import WhatsAppMessenger
from whatsapp_api import WhatsAppBusinessAPI

# Configuración inicial y definiciones
API_URL = "https://api-inference.huggingface.co/models/dataautogpt3/OpenDalleV1.1"
headers = {"Authorization": "Bearer {apikey}"}
token_whatsapp = 'EAAWLpi8brnoBO1qoWCRW0fqJAMUM1PeBB0ZCVJ3zinc7f58UDZANJSUiemAo1sfbh4WLfx3W6uqNjR6TAxg8yP267ZAf6OF3d9YHJZBGMskGdD6nbHBWTeC5PnoudSomF5jRCnaCM6k0Sw9o3ViSVYT66Qpz9n9F7dxHXDrHqKeZAAq1lQH6sNiPOccB8tbiR'
whatsapp_business_account_id = '240246142511300'
whatsapp_phone_number_id = '240246142511300'
DB_FILE = "stero.db"

messenger = WhatsAppMessenger(token_whatsapp)
api = WhatsAppBusinessAPI(token_whatsapp, whatsapp_business_account_id, whatsapp_phone_number_id)

templates = ['stero_picnic', 'stero_picnic_dos', 'stero_picnic_tres']

def inicializar_base_de_datos(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Creación de la tabla existente (si no has cambiado este proceso)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            wp TEXT,
            env TEXT,
            user_id INTEGER,
            enviado INTEGER DEFAULT 0
        )
    ''')
    
    # Creación de la nueva tabla para registrar respuestas y la imagen generada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wp TEXT,
            respuesta TEXT,
            image_path TEXT,
            fechaYhora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def obtener_numeros_pendientes():
    """Obtiene los números de teléfono a los que aún no se ha enviado un mensaje."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT wp FROM messages WHERE enviado = 0")
        numeros = cursor.fetchall()
        return [numero[0] for numero in numeros]

def marcar_como_enviado(telefono_envia):
    """Marca un número de teléfono como 'enviado' en la base de datos."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET enviado = 1 WHERE wp = ?", (telefono_envia,))
        conn.commit()

def enviar_mensaje(template_index, telefono_envia):
    """Envía un mensaje a un número de teléfono basado en un índice de template."""
    if template_index < len(templates):
        response = messenger.send_template_message(telefono_envia, templates[template_index])
        print(f"Mensaje enviado a {telefono_envia} con el template {templates[template_index]}: {response}")
        marcar_como_enviado(telefono_envia)
        return True
    else:
        print("Índice de template fuera de rango.")
        return False

def leer_mensaje_archivo():
    """Lee un mensaje de un archivo de texto y luego lo elimina."""
    try:
        with open("texto.txt", "r") as archivo:
            contenido = archivo.read()
            mensaje_recibido = re.search("Mensaje:(.*)", contenido).group(1).strip()
        # Intenta eliminar el archivo después de leerlo
        try:
            os.remove("texto.txt")
            print("Archivo texto.txt eliminado exitosamente.")
        except OSError as e:
            print(f"Error al eliminar el archivo texto.txt: {e}")
        return mensaje_recibido
    except FileNotFoundError:
        print("Archivo texto.txt no encontrado.")
        return None
    except AttributeError:
        print("El contenido del archivo no tiene el formato esperado.")
        return None

def numero_enviado(telefono_envia):
    """Verifica si un número de teléfono ya ha sido enviado."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT enviado FROM messages WHERE wp = ?", (telefono_envia,))
        resultado = cursor.fetchone()
        return resultado and resultado[0] == 1

def esperar_y_leer_respuesta():
    """Espera y lee la respuesta del archivo, con un tiempo máximo de espera."""
    tiempo_maximo_espera = 60  # segundos
    tiempo_inicio = time.time()
    while time.time() - tiempo_inicio < tiempo_maximo_espera:
        respuesta = leer_mensaje_archivo()
        if respuesta:
            return respuesta
        time.sleep(2)  # Espera 5 segundos antes de volver a intentar
    return None

def generar_y_enviar_imagen(texto_respuesta, numero_destino='573505556704'):
    payload = {
        "inputs": texto_respuesta,
    }
    links = [
        "https://api-inference.huggingface.co/models/dataautogpt3/OpenDalleV1.1",
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    ]
    
    image_path = None  # Inicializar image_path fuera del bucle

    for link in links:
        try:
            response = requests.post(link, headers=headers, json=payload)
            if response.status_code == 200:
                # La API ha retornado una imagen
                image_bytes = response.content
                image = Image.open(io.BytesIO(image_bytes))
                
                # Generar un nombre de archivo único para la imagen
                timestamp = int(time.time())
                image_path = f"generated_image_{timestamp}.png"
                image.save(image_path)
                
                # Subimos la imagen a WhatsApp y obtenemos el media_id
                upload_response = api.subir_imagen_whatsapp(image_path)
                if upload_response and 'id' in upload_response:
                    media_id = upload_response['id']
                    
                    # Enviamos la imagen al usuario
                    send_image_response = api.enviar_imagen_whatsapp(numero_destino, media_id)
                    print(f"Imagen enviada con éxito a {numero_destino}. Respuesta: {send_image_response}")
                    ms2 = messenger.send_template_message(numero_destino, 'stero_picnic_siete')
                    print(ms2)
                    # Retorna el path de la imagen solo si todo el proceso es exitoso
                    return image_path
                else:
                    print("Fallo al subir la imagen a WhatsApp.")
            else:
                print(f"Fallo al generar la imagen con {link}. Código de estado: {response.status_code}")
        except Exception as e:
            print(f"Excepción al intentar generar/subir/enviar la imagen con {link}: {e}")
            if image_path and os.path.exists(image_path):
                os.remove(image_path)  # Asegurarse de eliminar el archivo en caso de fallo

    print("No se pudo generar/enviar la imagen con ninguno de los enlaces proporcionados.")
    return None

def insertar_respuesta_en_bd(telefono_envia, respuesta, image_path):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO respuestas (wp, respuesta, image_path) VALUES (?, ?, ?)", (telefono_envia, respuesta, image_path))
        conn.commit()


def procesar_respuestas_dinamico():
    numeros_pendientes = obtener_numeros_pendientes()
    for telefono_envia in numeros_pendientes:
        if not numero_enviado(telefono_envia):
            respuestas_acumuladas = []  # Inicializa el acumulador de respuestas para este número
            ultimo_template_enviado = -1  # Inicializa el último índice de template enviado para este número

            for template_index in range(ultimo_template_enviado + 1, len(templates)):
                template = templates[template_index]
                if enviar_mensaje(template_index, telefono_envia):
                    print(f"Mensaje enviado a {telefono_envia} con el template {template}")
                    print(f"Esperando respuesta de {telefono_envia}...")
                    respuesta = esperar_y_leer_respuesta()
                    if respuesta:
                        print(f"Respuesta recibida de {telefono_envia}: {respuesta}")
                        respuestas_acumuladas.append(respuesta)  # Acumula la respuesta

                        if template_index == len(templates) - 1:
                            ms2 = messenger.send_template_message(telefono_envia, 'stero_picnic_seis')
                            print(ms2)
                            # Genera y envía la imagen basada en la última respuesta (u otra lógica si prefieres)
                            image_path = generar_y_enviar_imagen(respuesta, telefono_envia)
                            if image_path:
                                # Concatena todas las respuestas acumuladas para insertarlas en la BD
                                todas_las_respuestas = " ".join(respuestas_acumuladas)
                                insertar_respuesta_en_bd(telefono_envia, todas_las_respuestas, image_path)
                            else:
                                print("Fallo al generar o enviar la imagen.")
                        ultimo_template_enviado = template_index  # Actualiza el último índice de template enviado

                    else:
                        print(f"No se recibió respuesta de {telefono_envia}.")
                        break  # Si no se recibe respuesta, detener el proceso para este número
                else:
                    print(f"Error al enviar mensaje al número {telefono_envia}. Deteniendo proceso para este número.")
                    break
                time.sleep(1)  # Espera entre mensajes
        else:
            print(f"El número {telefono_envia} ya ha sido enviado. No se enviará nuevamente.")

if __name__ == "__main__":
    inicializar_base_de_datos(DB_FILE)
    try:
        while True:
            procesar_respuestas_dinamico()
            time.sleep(5)  # Espera un poco antes de volver a revisar la base de datos.
    except KeyboardInterrupt:
        print("Interrupción por el usuario, cerrando...")


   

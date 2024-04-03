import requests
import json

class WhatsAppBusinessAPI:
    def __init__(self, token_whatsapp, whatsapp_business_account_id, whatsapp_phone_number_id):
        self.token_whatsapp = token_whatsapp
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.whatsapp_phone_number_id = whatsapp_phone_number_id

    def subir_imagen_whatsapp(self, ruta_imagen):
        api_url = f"https://graph.facebook.com/v19.0/{self.whatsapp_business_account_id}/media"
        headers = {'Authorization': f'Bearer {self.token_whatsapp}'}
        data = {'messaging_product': 'whatsapp'}
        files = {'file': (ruta_imagen, open(ruta_imagen, 'rb'), 'image/png')}

        try:
            respuesta = requests.post(api_url, headers=headers, data=data, files=files)
            respuesta_json = respuesta.json()
            if 'id' in respuesta_json:
                return respuesta_json
            else:
                print("La respuesta no contiene un 'id'. Aquí está la respuesta completa para depuración:", respuesta_json)
                return None
        except requests.exceptions.RequestException as e:
            print("Ocurrió un error al realizar la solicitud a la API:", e)
            return None

    def enviar_imagen_whatsapp(self, numero_destino, media_id):
        api_url = f"https://graph.facebook.com/v19.0/{self.whatsapp_phone_number_id}/messages"
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.token_whatsapp}'}
        data = {"messaging_product": "whatsapp", "to": numero_destino, "type": "image", "image": {"id": media_id}}

        respuesta = requests.post(api_url, headers=headers, data=json.dumps(data))
        return respuesta.json()

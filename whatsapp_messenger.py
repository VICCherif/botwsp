import requests
import json

class WhatsAppMessenger:
    def __init__(self, access_token):
        self.access_token = access_token
        self.url = "https://graph.facebook.com/v18.0/240246142511300/messages"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def send_template_message(self, recipient_id, template_name, language_code="es"):
        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        })

        response = requests.request("POST", self.url, headers=self.headers, data=payload)
        return response.text

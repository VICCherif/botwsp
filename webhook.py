from flask import Flask, jsonify, request
import os


app = Flask(__name__)

port = os.environ.get('PORT', 5000)


@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    if request.method == "GET":
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == "SteroPicnicApiSegment":
            return challenge
        else:
            return "Error de autenticación.", 403

    elif request.method == "POST":
        try:
            data = request.get_json()
            # Asegúrate de que los datos se recibieron correctamente
            if data and 'entry' in data and data['entry']:
                entry = data['entry'][0]
                if 'changes' in entry and entry['changes']:
                    changes = entry['changes'][0]
                    if 'value' in changes:
                        value = changes['value']
                        if 'messages' in value and value['messages']:
                            message = value['messages'][0]
                            if 'from' in message and 'text' in message and 'body' in message['text']:
                                from_number = message['from']
                                message_body = message['text']['body']
                                mensaje = f"Telefono:{from_number}|Mensaje:{message_body}"
                                
                                # Escribir el mensaje en un archivo
                                with open("texto.txt", "w") as f:
                                    f.write(mensaje)
                                
                                return jsonify({"status": "success"}), 200
            # Si algo falla, devuelve un error
            return jsonify({"error": "Estructura del JSON no reconocida"}), 400
        except Exception as e:
            # Manejar cualquier otro tipo de error inesperado
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(port))

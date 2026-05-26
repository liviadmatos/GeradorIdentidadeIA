# app.py (Parte 1)
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importando o que criamos no outro arquivo:
from config import LOOKS_SCHEMA, SYSTEM_INSTRUCTION

# Carrega as variáveis de ambiente e inicia o Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Inicializa o Flask
app = Flask(__name__)
CORS(app)

# app.py (Parte 2)

def generate_look(pecas, clima, ocasiao):
    # Monta um resumo das peças enviadas para o prompt
    lista_pecas = ", ".join(pecas)
    conteudo_prompt = f"""
Monte um look completo usando SOMENTE peças desta lista:

{lista_pecas}

Clima: {clima}
Ocasião: {ocasiao}

Monte um look apropriado, coerente e esteticamente harmonioso para esse clima e ocasião.

Lembre-se:
- o look deve estar completo
- usar apenas peças fornecidas
- incluir obrigatoriamente um calçado
- usar vestido OU combinação de parte superior + parte inferior
"""

    # Faz a chamada para o modelo pedindo uma resposta estruturada em JSON
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json", # Força a saída em formato JSON
            response_schema=LOOKS_SCHEMA,       # Segue o esquema do config.py
        )
    )
    return response.text

# app.py (Parte 3)

@app.route("/")
def root():
    return jsonify({
        "status": "success",
        "message": "API Gerador de Looks funcionando!",
        "version": "1.0"
    }), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    
    # Validação 1: O JSON foi enviado?
    if not data or ("pecas" not in data and "peças" not in data):
        return jsonify({
            "status": "error",
            "message": "Por favor, envie uma lista de peças no formato JSON."
        }), 400

    pecas = data.get("pecas", data.get("peças", []))
    clima = data.get("clima")
    ocasiao = data.get("ocasiao")

    # Validação 2: É uma lista e possui no mínimo 3 itens?
    if not isinstance(pecas, list) or len(pecas) < 3:
        return jsonify({
            "status": "error",
            "message": "Você precisa fornecer no mínimo 3 peças."
        }), 400

    if not clima or not isinstance(clima, str):
        return jsonify({
            "status": "error",
            "message": "Por favor, informe o clima para o look."
        }), 400

    if not ocasiao or not isinstance(ocasiao, str):
        return jsonify({
            "status": "error",
            "message": "Por favor, informe a ocasião para o look."
        }), 400

    try:
        # Pede para o Gemini gerar o look (retorna como string JSON)
        look_json_string = generate_look(pecas, clima, ocasiao)

        # Converte a string JSON em Dicionário Python para o Flask organizar a resposta
        look_estruturado = json.loads(look_json_string)

        return jsonify({
            "status": "success",
            "pecas_enviadas": pecas,
            "clima": clima,
            "ocasiao": ocasiao,
            "dados_look": look_estruturado
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao gerar o look: {str(e)}"
        }), 500

# Executa o servidor local
if __name__ == "__main__":
    app.run(debug=True)


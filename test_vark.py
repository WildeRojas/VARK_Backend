import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# 🔑 Cargar el archivo .env automáticamente
# Busca el .env en la misma carpeta donde está este script
load_dotenv(Path(__file__).parent / ".env")

def verificar_api_key():
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ No se encontró GROQ_API_KEY en el .env ni en variables de entorno.")
        return False

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Responde solo con OK."}],
            max_tokens=5,
            temperature=0
        )
        print("✅ ¡API Key válida y funcional!")
        print(f"🤖 Respuesta: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        error = str(e).lower()
        if "api_key" in error or "auth" in error:
            print("❌ La API Key es inválida o está desactivada.")
        else:
            print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    verificar_api_key()
# src/gemini_client.py

import os
import requests
import base64
import google.generativeai as genai
from dotenv import load_dotenv
from config.prompts import SYSTEM_PROMPT, STORY_SHARE_CAPTION_PROMPT

load_dotenv()


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.vision_model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_response(self, user_message: str, conversation_history: list = None, temperature: float = 0.85) -> str:
        """Genera respuesta de texto con historial de conversación."""
        try:
            # Construir el prompt con historial
            full_prompt = SYSTEM_PROMPT + "\n\n"

            if conversation_history:
                full_prompt += "HISTORIAL DE CONVERSACIÓN RECIENTE:\n"
                for item in conversation_history[-6:]:  # últimos 6 intercambios
                    full_prompt += f"Usuario: {item['message']}\nValeria: {item['response']}\n"
                full_prompt += "\n"

            full_prompt += f"Usuario: {user_message}\nValeria:"

            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=300,
                )
            )
            return response.text.strip()

        except Exception as e:
            print(f"❌ Error Gemini texto: {e}")
            return "Hola! 😊 Ahora mismo no puedo responder bien, pero escríbeme en un momento!"

    def generate_response_with_image(self, image_url: str, caption: str = "", conversation_history: list = None) -> str:
        """Genera respuesta analizando una imagen enviada por el usuario."""
        try:
            # Descargar la imagen
            img_response = requests.get(image_url, timeout=10)
            img_data = base64.b64encode(img_response.content).decode("utf-8")

            # Detectar tipo de contenido
            content_type = img_response.headers.get("Content-Type", "image/jpeg")

            prompt_parts = [
                SYSTEM_PROMPT + "\n\n",
            ]

            if conversation_history:
                history_text = "HISTORIAL RECIENTE:\n"
                for item in conversation_history[-4:]:
                    history_text += f"Usuario: {item['message']}\nValeria: {item['response']}\n"
                prompt_parts.append(history_text + "\n")

            if caption:
                prompt_parts.append(f"El usuario envió una imagen con el texto: '{caption}'\n")
            else:
                prompt_parts.append("El usuario envió esta imagen:\n")

            prompt_parts.append(
                genai.types.BlobDict(data=img_data, mime_type=content_type)  # type: ignore
            )

            prompt_parts.append(
                "\nDescribe brevemente lo que ves en la imagen e interpreta el contexto "
                "(si es un emoji, meme, foto, etc.). Luego responde de forma natural y "
                "cálida como Valeria, la community manager. Respuesta corta (1-2 oraciones)."
            )

            response = self.vision_model.generate_content(
                prompt_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.85,
                    max_output_tokens=200,
                )
            )
            return response.text.strip()

        except Exception as e:
            print(f"❌ Error Gemini imagen: {e}")
            # Fallback: responder al caption si hay
            if caption:
                return self.generate_response(f"[El usuario envió una imagen con el texto: {caption}]", conversation_history)
            return "Qué bonita imagen! 😍 gracias por compartirla"

    def generate_comment_reply(self, comment_text: str, post_description: str = "") -> str:
        """Genera respuesta a un comentario de una publicación."""
        try:
            prompt = SYSTEM_PROMPT + "\n\n"
            prompt += "Estás respondiendo a un comentario en una publicación de la página.\n"

            if post_description:
                prompt += f"La publicación es sobre: {post_description}\n"

            prompt += f"\nComentario del usuario: {comment_text}\n"
            prompt += "Valeria (respuesta breve, cálida, que enganche con la página):"

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.85,
                    max_output_tokens=150,
                )
            )
            return response.text.strip()

        except Exception as e:
            print(f"❌ Error Gemini comentario: {e}")
            return "Gracias por tu comentario! 😊✨"

    def generate_story_caption(self, post_message: str) -> str:
        """Genera un texto atractivo para compartir una publicación en historias."""
        try:
            prompt = STORY_SHARE_CAPTION_PROMPT + f"\n\nPublicación: {post_message}\nTexto para historia:"

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=100,
                )
            )
            return response.text.strip()

        except Exception as e:
            print(f"❌ Error generando caption historia: {e}")
            return "✨ Nuevo contenido en la página! No te lo pierdas 🔥"

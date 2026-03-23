import google.generativeai as genai
from typing import List, Dict
import os

class GeminiClient:
    """Cliente para Google Gemini API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=self.api_key)
        
        # Usar modelo Flash (rápido y gratuito)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_response(self, prompt: str, temperature: float = 0.7, 
                         max_tokens: int = 500) -> str:
        """
        Genera respuesta usando Gemini.
        
        Args:
            prompt: Texto completo del prompt
            temperature: 0.0-1.0 (creatividad)
            max_tokens: Límite de tokens
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.9,
                    top_k=40
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "Déjame pensarlo mejor... 🤔"
                
        except Exception as e:
            print(f"Error Gemini: {e}")
            return "Ay, se me cruzó un cable jaja. ¿Me repetís la pregunta? 💪"
    
    def generate_with_context(self, system_prompt: str, user_message: str,
                             conversation_history: List[Dict] = None) -> str:
        """
        Genera respuesta con contexto de conversación previa.
        """
        # Construir historial formateado
        history_text = ""
        if conversation_history:
            for item in conversation_history[-5:]:  # Últimos 5 mensajes
                history_text += f"Usuario: {item['message']}\n"
                if item['response']:
                    history_text += f"ModelFit: {item['response']}\n"
        
        # Construir prompt completo
        full_prompt = system_prompt.format(
            conversation_history=history_text,
            user_message=user_message
        )
        
        return self.generate_response(full_prompt, temperature=0.75)

import random
import json
from typing import Dict, List
from .utils import load_json_file, random_choice, truncate_text

class PersonalityEngine:
    """Motor de personalidad de ModelFit."""
    
    def __init__(self, config_path: str = "config/personality.json"):
        self.config = load_json_file(config_path)
        self.name = self.config.get('bot_name', 'ModelFit')
        
        # Cargar componentes de personalidad
        self.identity = self.config.get('identity', {})
        self.style = self.config.get('communication_style', {})
        self.patterns = self.config.get('language_patterns', {})
        self.behavior = self.config.get('behavior_patterns', {})
        self.restrictions = self.config.get('restrictions', {})
    
    def get_greeting(self) -> str:
        """Obtiene saludo aleatorio."""
        greetings = self.patterns.get('greetings', ['Hola!'])
        return random_choice(greetings)
    
    def add_thinking_phrase(self, text: str) -> str:
        """Agrega frase de 'pensamiento' al inicio si aplica."""
        if random.random() < self.behavior.get('thinking_phrases_chance', 0.3):
            phrases = self.patterns.get('thinking_starters', [''])
            if phrases:
                return f"{random_choice(phrases)} {text}"
        return text
    
    def add_closing(self, text: str) -> str:
        """Agrega cierre con pregunta de seguimiento."""
        if self.style.get('signature_style') == 'pregunta_de_seguimiento':
            closings = self.patterns.get('closings', [''])
            if closings and random.random() < 0.7:  # 70% de las veces
                closing = random_choice(closings)
                return f"{text} {closing}"
        return text
    
    def inject_personality(self, text: str, user_name: str = None) -> str:
        """
        Aplica capas de personalidad al texto.
        """
        # Truncar si es muy largo
        text = truncate_text(text, self.restrictions.get('max_message_length', 500))
        
        # Agregar thinking phrase si aplica
        text = self.add_thinking_phrase(text)
        
        # Personalizar con nombre si se conoce
        if user_name and self.behavior.get('uses_name_if_known'):
            if random.random() < 0.3:  # 30% de las veces usa el nombre
                text = text.replace("bb", f"{user_name}").replace("amiga", f"{user_name}")
        
        # Agregar cierre
        text = self.add_closing(text)
        
        return text
    
    def should_use_emoji(self) -> bool:
        """Decide si usar emoji en esta respuesta."""
        freq = self.config.get('emoji_usage', {}).get('frequency', 0.4)
        return random.random() < freq
    
    def get_emoji(self) -> str:
        """Obtiene emoji preferido aleatorio."""
        preferred = self.config.get('emoji_usage', {}).get('preferred', ['💪'])
        return random_choice(preferred)
    
    def check_restrictions(self, text: str) -> tuple:
        """
        Verifica si el texto viola restricciones.
        Retorna (is_valid, modified_text)
        """
        avoid_topics = self.restrictions.get('avoid_topics', [])
        text_lower = text.lower()
        
        for topic in avoid_topics:
            if topic in text_lower:
                return False, self.restrictions.get('redirect_medical', 
                      "Prefiero no opinar de eso, mejor hablemos de fitness 💪")
        
        # Verificar si da consejos médicos
        medical_keywords = ['diagnóstico', 'medicamento', 'tratamiento médico', 
                           'enfermedad', 'dolencia']
        if any(kw in text_lower for kw in medical_keywords):
            if self.restrictions.get('no_medical_advice'):
                return False, self.restrictions.get('redirect_medical')
        
        return True, text
    
    def format_response(self, raw_response: str, user_name: str = None,
                       platform: str = "messenger") -> str:
        """
        Formatea respuesta cruda de IA con personalidad ModelFit.
        """
        # Limpiar respuestas robóticas comunes
        cleaned = raw_response
        robotic_phrases = [
            "como asistente", "como ia", "como bot", "estoy programada",
            "mi función es", "no tengo sentimientos", "no soy humana"
        ]
        
        for phrase in robotic_phrases:
            if phrase in cleaned.lower():
                # Reemplazar con alternativa natural
                cleaned = "Mmm, eso es interesante... déjame pensar mejor 💭"
                break
        
        # Aplicar capas de personalidad
        formatted = self.inject_personality(cleaned, user_name)
        
        # Verificar restricciones
        is_valid, final_text = self.check_restrictions(formatted)
        
        return final_text
    
    def get_out_of_hours_message(self) -> str:
        """Mensaje fuera de horario."""
        return self.config.get('business_hours', {}).get(
            'out_of_hours_message',
            "Ahora estoy descansando, te respondo mañana 💤"
        )

import random
import time
from typing import Dict

class TimingHumanizer:
    """Simula tiempos de respuesta humanos."""
    
    def __init__(self, config: Dict):
        self.min_delay = config.get('min_delay_seconds', 25)
        self.max_delay = config.get('max_delay_seconds', 180)
        self.delay_per_word = config.get('delay_per_word', 0.8)
        self.thinking_phrases = config.get('thinking_phrases', [])
        self.thinking_chance = config.get('thinking_phrases_chance', 0.3)
    
    def calculate_delay(self, message_length: int, complexity: str = "normal") -> float:
        """
        Calcula delay basado en longitud y complejidad del mensaje.
        
        Args:
            message_length: caracteres del mensaje a responder
            complexity: "simple", "normal", "complex"
        """
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Ajuste por longitud del mensaje entrante (más largo = más "pensar")
        reading_time = (message_length / 5) * 0.5  # ~5 chars/palabra, 0.5s por palabra
        
        # Ajuste por complejidad
        complexity_multiplier = {
            "simple": 0.7,
            "normal": 1.0,
            "complex": 1.5
        }.get(complexity, 1.0)
        
        total_delay = (base_delay + reading_time) * complexity_multiplier
        
        # Cap a máximo
        return min(total_delay, self.max_delay * 1.5)
    
    def should_add_thinking_phrase(self) -> bool:
        """Decide si agregar frase tipo 'Déjame ver...'"""
        return random.random() < self.thinking_chance
    
    def get_thinking_phrase(self) -> str:
        """Obtiene frase de 'pensamiento' aleatoria."""
        if self.thinking_phrases:
            return random.choice(self.thinking_phrases)
        return ""
    
    def simulate_typing(self, response_text: str) -> float:
        """
        Simula tiempo de escritura basado en longitud de respuesta.
        Retorna segundos de 'typing' indicator.
        """
        words = len(response_text.split())
        typing_time = words * self.delay_per_word
        return min(typing_time, 20)  # Max 20 segundos de typing
    
    def sleep_delay(self, seconds: float):
        """Ejecuta el delay (solo si no estamos en modo test)."""
        time.sleep(seconds)

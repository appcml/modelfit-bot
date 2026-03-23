import random
import json
from datetime import datetime
from typing import Dict, Any

def load_json_file(path: str) -> Dict[str, Any]:
    """Carga archivo JSON de configuración."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def get_current_hour_santiago() -> int:
    """Obtiene hora actual en Santiago de Chile."""
    from datetime import datetime
    import pytz
    
    try:
        tz = pytz.timezone('America/Santiago')
        return datetime.now(tz).hour
    except:
        # Fallback sin pytz
        return datetime.now().hour

def is_business_hours(config: Dict) -> bool:
    """Verifica si está en horario de atención."""
    if not config.get('business_hours', {}).get('enabled', False):
        return True
    
    current_hour = get_current_hour_santiago()
    start = int(config['business_hours']['start'].split(':')[0])
    end = int(config['business_hours']['end'].split(':')[0])
    
    return start <= current_hour < end

def random_choice(options: list, weights: list = None) -> Any:
    """Selecciona opción aleatoria, opcionalmente con pesos."""
    if weights:
        return random.choices(options, weights=weights, k=1)[0]
    return random.choice(options)

def truncate_text(text: str, max_length: int = 500) -> str:
    """Trunca texto si excede máximo."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

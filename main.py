#!/usr/bin/env python3
"""
ModelFit Bot - Punto de entrada principal
Responde mensajes, comentarios y comparte posts en historias de Facebook
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modelfit_bot import ModelFitBot

if __name__ == "__main__":
    bot = ModelFitBot()
    # Revisa mensajes y comentarios cada 5 minutos (300 segundos)
    # Puedes cambiar el intervalo según tus necesidades
    bot.run_forever(interval_seconds=300)

#!/usr/bin/env python3
"""
ModelFit Bot - Asistente virtual de fitness
Ejecutar: python main.py
"""

import sys
import os

# Asegurar que src está en path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modelfit_bot import ModelFitBot

def main():
    """Función principal."""
    try:
        # Inicializar bot
        bot = ModelFitBot()
        
        # Ejecutar un ciclo de procesamiento
        bot.run_cycle()
        
        print("🎯 ModelFit Bot completó su ciclo exitosamente")
        
    except Exception as e:
        print(f"💥 Error fatal en ModelFit Bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

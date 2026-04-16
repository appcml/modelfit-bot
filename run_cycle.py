#!/usr/bin/env python3
"""
run_cycle.py - Ejecuta UN solo ciclo del bot.
Diseñado para GitHub Actions: se llama cada 5 minutos por el scheduler.
No hace loop infinito, solo procesa lo que hay ahora y termina.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modelfit_bot import ModelFitBot

if __name__ == "__main__":
    print("🤖 Iniciando ciclo del bot...")
    bot = ModelFitBot()
    bot.run_cycle()
    print("✅ Ciclo completado")

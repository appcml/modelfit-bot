#!/usr/bin/env python3
"""
ModelFit Bot - Versión Debug
Muestra información detallada de conexión
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🏋️  MODELFIT BOT - MODO DEBUG")
print("=" * 60)
print()

# Test 1: Verificar variables de entorno
print("🔍 [1] Verificando variables de entorno...")
print(f"    GEMINI_API_KEY: {'✅ Configurada' if os.getenv('GEMINI_API_KEY') else '❌ No encontrada'}")
print(f"    META_PAGE_ACCESS_TOKEN: {'✅ Configurada' if os.getenv('META_PAGE_ACCESS_TOKEN') else '❌ No encontrada'}")
print(f"    META_PAGE_ID: {'✅ Configurada' if os.getenv('META_PAGE_ID') else '❌ No encontrada'}")
print()

# Test 2: Probar conexión Meta API
print("🔍 [2] Probando conexión con Facebook...")
try:
    from src.meta_api import MetaAPI
    api = MetaAPI()
    print(f"    ✅ MetaAPI inicializada")
    print(f"    Page ID: {api.page_id}")
    print(f"    Token: {api.access_token[:20]}...")
    
    # Probar lectura de conversaciones
    print()
    print("    📨 Leyendo conversaciones...")
    messages = api.get_unread_messages(limit=5)
    print(f"    ✅ Encontradas: {len(messages)} conversaciones")
    
    for i, msg in enumerate(messages, 1):
        print(f"       [{i}] {msg['from_name']}: {msg['text'][:50]}...")
        
except Exception as e:
    print(f"    ❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 3: Probar Gemini
print("🔍 [3] Probando conexión con Gemini...")
try:
    from src.gemini_client import GeminiClient
    gemini = GeminiClient()
    print(f"    ✅ GeminiClient inicializado")
    
    # Test simple
    test_response = gemini.generate_response("Responde solo 'OK' si funciona", temperature=0.1)
    print(f"    ✅ Test de respuesta: {test_response[:50]}...")
    
except Exception as e:
    print(f"    ❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 4: Probar base de datos
print("🔍 [4] Probando base de datos...")
try:
    from src.conversation_memory import ConversationMemory
    memory = ConversationMemory()
    print(f"    ✅ ConversationMemory inicializada")
    print(f"    Ruta DB: database/conversations.db")
    
    # Test escritura
    memory.add_interaction(
        user_id="test_user",
        platform="test",
        message="Mensaje de prueba",
        response="Respuesta de prueba"
    )
    print(f"    ✅ Test de escritura exitoso")
    
    # Test lectura
    history = memory.get_conversation_history("test_user", limit=1)
    print(f"    ✅ Test de lectura exitoso: {len(history)} registros")
    
except Exception as e:
    print(f"    ❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 5: Ejecutar ciclo completo (solo si todo lo anterior funcionó)
print("🔍 [5] Ejecutando ciclo completo del bot...")
print()

try:
    from src.modelfit_bot import ModelFitBot
    bot = ModelFitBot()
    
    print("    ✅ Bot inicializado correctamente")
    print("    🚀 Ejecutando ciclo...")
    print()
    
    bot.run_cycle()
    
    print()
    print("    ✅ CICLO COMPLETADO CON ÉXITO")
    
except Exception as e:
    print(f"    ❌ Error en ciclo: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("🏁 DEBUG FINALIZADO")
print("=" * 60)

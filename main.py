#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# DEBUG SIMPLE
from src.meta_api import MetaAPI

print("🔍 TEST DE CONEXIÓN")
try:
    api = MetaAPI()
    print(f"✅ API inicializada")
    print(f"   Page ID: {api.page_id}")
    print(f"   Token: {api.access_token[:15]}...")
    
    # Probar lectura
    print("\n📨 Probando leer mensajes...")
    msgs = api.get_unread_messages(limit=5)
    print(f"   Encontrados: {len(msgs)} mensajes")
    
    for m in msgs:
        print(f"   - {m['from_name']}: {m['text'][:40]}...")
        
    print("\n💬 Probando leer comentarios...")
    comments = api.get_recent_comments(post_limit=3)
    print(f"   Encontrados: {len(comments)} comentarios")
    
    print("\n✅ TODO FUNCIONA - El bot debería responder")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

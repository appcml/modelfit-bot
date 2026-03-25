import os
import random
from typing import List, Dict
from datetime import datetime

from .conversation_memory import ConversationMemory
from .gemini_client import GeminiClient
from .personality_engine import PersonalityEngine
from .timing_humanizer import TimingHumanizer
from .meta_api import MetaAPI
from .utils import is_business_hours
from config.prompts import SYSTEM_PROMPT, COMMENT_PROMPT


class ModelFitBot:
    """Bot principal de ModelFit."""
    
    def __init__(self):
        print(f"🏋️  Iniciando ModelFit Bot...")
        
        # Inicializar componentes
        self.memory = ConversationMemory()
        self.gemini = GeminiClient()
        self.personality = PersonalityEngine()
        self.timing = TimingHumanizer(self.personality.behavior)
        self.meta = MetaAPI()
        
        # Configuración
        self.max_daily_messages = int(os.getenv('MAX_DAILY_MESSAGES', 50))
        self.name = "ModelFit"
        
        print(f"✅ {self.name} lista para responder")
    
    def process_message(self, user_id: str, user_name: str, text: str,
                       platform: str = "messenger") -> bool:
        """
        Procesa un mensaje directo y responde.
        """
        print(f"📩 Mensaje de {user_name} ({user_id}): {text[:60]}...")
        
        # Verificar rate limiting
        daily_count = self.memory.get_daily_message_count(user_id)
        print(f"    Mensajes hoy de este usuario: {daily_count}/{self.max_daily_messages}")
        
        if daily_count >= self.max_daily_messages:
            print(f"    ⚠️  Usuario excedió límite diario")
            return False
        
        # Verificar horario de atención
        if not is_business_hours(self.personality.config):
            out_msg = self.personality.get_out_of_hours_message()
            print(f"    🌙 Fuera de horario, enviando mensaje automático")
            self.meta.send_message(user_id, out_msg)
            return True
        
        # Obtener historial de conversación
        history = self.memory.get_conversation_history(user_id, limit=5)
        print(f"    Historial: {len(history)} mensajes previos")
        
        # Calcular delay humanizado
        complexity = self._assess_complexity(text)
        delay = self.timing.calculate_delay(len(text), complexity)
        print(f"    ⏱️  Delay calculado: {delay:.1f}s (complejidad: {complexity})")
        
        # Generar respuesta con Gemini
        print(f"    🤖 Generando respuesta con Gemini...")
        raw_response = self.gemini.generate_with_context(
            SYSTEM_PROMPT, text, history
        )
        print(f"    Respuesta cruda: {raw_response[:60]}...")
        
        # Aplicar personalidad ModelFit
        final_response = self.personality.format_response(
            raw_response, user_name, platform
        )
        print(f"    Respuesta final: {final_response[:60]}...")
        
        # Simular typing indicator
        typing_time = self.timing.simulate_typing(final_response)
        print(f"    ⌨️  Simulando escritura: {typing_time:.1f}s")
        
        self.meta.send_typing_indicator(user_id)
        self.timing.sleep_delay(delay)
        
        # Enviar respuesta
        print(f"    📤 Enviando mensaje...")
        success = self.meta.send_message(user_id, final_response, typing_time)
        
        if success:
            # Guardar en memoria
            self.memory.add_interaction(
                user_id=user_id,
                platform=platform,
                message=text,
                response=final_response,
                metadata={'complexity': complexity, 'delay': delay}
            )
            print(f"    ✅ Mensaje enviado y guardado")
        else:
            print(f"    ❌ Falló el envío")
        
        return success
    
    def process_comment(self, comment_id: str, user_id: str, user_name: str,
                       text: str, post_id: str) -> bool:
        """
        Procesa y responde a un comentario.
        """
        print(f"💬 Comentario de {user_name}: {text[:60]}...")
        
        # Generar respuesta más breve para comentarios
        prompt = COMMENT_PROMPT.format(comment_text=text)
        print(f"    🤖 Generando respuesta...")
        raw_response = self.gemini.generate_response(prompt, temperature=0.6, 
                                                     max_tokens=150)
        
        # Aplicar personalidad (más concisa para comentarios)
        final_response = self.personality.format_response(raw_response, user_name)
        
        # Limitar longitud para comentarios
        if len(final_response) > 200:
            final_response = final_response[:197] + "..."
            print(f"    ✂️  Truncado a 200 caracteres")
        
        # Delay más corto para comentarios
        delay = random.uniform(15, 45)
        print(f"    ⏱️  Delay: {delay:.1f}s")
        self.timing.sleep_delay(delay)
        
        # Responder al comentario
        print(f"    📤 Publicando respuesta...")
        success = self.meta.reply_to_comment(comment_id, final_response)
        
        if success:
            # Guardar en memoria como interacción
            self.memory.add_interaction(
                user_id=user_id,
                platform="facebook_comment",
                message=text,
                response=final_response,
                metadata={'post_id': post_id, 'comment_id': comment_id}
            )
            print(f"    ✅ Comentario respondido")
        else:
            print(f"    ❌ Falló la respuesta")
        
        return success
    
    def run_cycle(self):
        """
        Ciclo principal: revisa mensajes y comentarios nuevos.
        """
        print(f"\n{'='*60}")
        print(f"🔄 CICLO MODELFIT - {datetime.now()}")
        print(f"{'='*60}")
        
        messages_processed = 0
        comments_processed = 0
        
        # 1. Procesar mensajes directos
        try:
            print(f"\n📨 [MENSAJES] Buscando mensajes sin leer...")
            unread = self.meta.get_unread_messages(limit=10)
            print(f"    → Encontrados: {len(unread)} mensajes")
            
            for i, msg in enumerate(unread, 1):
                print(f"\n    ─────────────────────────────")
                print(f"    [{i}/{len(unread)}] De: {msg['from_name']} ({msg['from_id']})")
                print(f"         Texto: {msg['text'][:80]}...")
                print(f"         Fecha: {msg['created_time']}")
                
                result = self.process_message(
                    user_id=msg['from_id'],
                    user_name=msg['from_name'],
                    text=msg['text'],
                    platform="messenger"
                )
                
                if result:
                    messages_processed += 1
                    # Marcar como leído
                    mark_result = self.meta.mark_as_read(msg['conversation_id'])
                    print(f"         Marcado como leído: {'✅' if mark_result else '❌'}")
                else:
                    print(f"         ⚠️  No se pudo procesar")
                    
        except Exception as e:
            print(f"    ❌ ERROR en mensajes: {str(e)}")
            import traceback
            traceback.print_exc()

        # 2. Procesar comentarios
        try:
            print(f"\n💬 [COMENTARIOS] Buscando comentarios recientes...")
            comments = self.meta.get_recent_comments(post_limit=5)
            recent_comments = self._filter_recent(comments, hours=2)
            print(f"    → Comentarios recientes (2h): {len(recent_comments)}")
            
            for i, comment in enumerate(recent_comments, 1):
                print(f"\n    ─────────────────────────────")
                print(f"    [{i}/{len(recent_comments)}] De: {comment['from_name']}")
                print(f"         Texto: {comment['text'][:80]}...")
                print(f"         Post: {comment['post_id'][:20]}...")
                
                if self._already_responded(comment['from_id'], comment['text']):
                    print(f"         ⏭️  Ya respondido anteriormente, saltando")
                    continue
                
                result = self.process_comment(
                    comment_id=comment['id'],
                    user_id=comment['from_id'],
                    user_name=comment['from_name'],
                    text=comment['text'],
                    post_id=comment['post_id']
                )
                
                if result:
                    comments_processed += 1
                    
        except Exception as e:
            print(f"    ❌ ERROR en comentarios: {str(e)}")
            import traceback
            traceback.print_exc()

        print(f"\n{'='*60}")
        print(f"📊 RESUMEN DEL CICLO")
        print(f"    Mensajes respondidos: {messages_processed}")
        print(f"    Comentarios respondidos: {comments_processed}")
        print(f"    Total interacciones: {messages_processed + comments_processed}")
        print(f"{'='*60}\n")
    
    def _assess_complexity(self, text: str) -> str:
        """Evalúa complejidad del mensaje para timing."""
        text_lower = text.lower()
        
        # Preguntas complejas
        complex_indicators = ['por qué', 'cómo', 'explica', 'recomienda', 
                             'opinión', 'piensas', 'dieta', 'rutina completa',
                             'plan', 'nutrición', 'suplementos']
        if any(ind in text_lower for ind in complex_indicators):
            return "complex"
        
        # Mensajes simples
        simple_indicators = ['hola', 'gracias', 'ok', 'jaja', '❤️', '🔥', '👍', 'holi']
        if any(ind in text_lower for ind in simple_indicators) and len(text) < 20:
            return "simple"
        
        return "normal"
    
    def _filter_recent(self, items: List[Dict], hours: int = 2) -> List[Dict]:
        """Filtra items por tiempo (últimas N horas)."""
        from datetime import datetime, timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for item in items:
            try:
                created = datetime.fromisoformat(
                    item['created_time'].replace('Z', '+00:00')
                )
                if created > cutoff:
                    recent.append(item)
            except:
                # Si no podemos parsear fecha, incluir por si acaso
                recent.append(item)
        
        return recent
    
    def _already_responded(self, user_id: str, text: str) -> bool:
        """
        Verifica si ya respondimos algo similar recientemente.
        """
        # Obtener últimas interacciones del usuario
        history = self.memory.get_conversation_history(user_id, limit=3)
        
        for item in history:
            # Si el mensaje entrante es muy similar a uno previo
            if self._similarity(text, item['message']) > 0.8:
                return True
            # Si ya respondimos en los últimos 10 minutos
            try:
                msg_time = datetime.fromisoformat(item['timestamp'])
                if (datetime.now() - msg_time).seconds < 600:  # 10 min
                    return True
            except:
                pass
        
        return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Simplicidad: similaridad básica por palabras."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

# src/modelfit_bot.py

import time
import random
import os
from datetime import datetime
from src.meta_api import MetaAPI
from src.gemini_client import GeminiClient
from src.conversation_memory import ConversationMemory

# ─── CONFIGURACIÓN DE DELAYS (simula comportamiento humano) ──────────────────
# Si BOT_NO_DELAY=true (GitHub Actions), los delays se saltan.
# En producción local (main.py) los delays funcionan normalmente.

NO_DELAY = os.environ.get("BOT_NO_DELAY", "false").lower() == "true"

MSG_DELAY_MIN = 60       # 1 minuto
MSG_DELAY_MAX = 480      # 8 minutos
COMMENT_DELAY_MIN = 120  # 2 minutos
COMMENT_DELAY_MAX = 600  # 10 minutos
TYPING_MIN = 3
TYPING_MAX = 12

def _sleep(seconds: int):
    """Duerme solo si no estamos en modo sin delay."""
    if NO_DELAY:
        print(f"  ⏩ Delay omitido ({seconds}s) — modo GitHub Actions")
        return
    time.sleep(seconds)

# Cada cuántos ciclos revisar si hay posts nuevos para compartir en historias
STORY_CHECK_EVERY_N_CYCLES = 6  # cada ~6 ciclos (ajusta según frecuencia del loop)

# ─────────────────────────────────────────────────────────────────────────────


class ModelFitBot:
    def __init__(self):
        self.api = MetaAPI()
        self.gemini = GeminiClient()
        self.memory = ConversationMemory()
        self._cycle_count = 0
        self._replied_messages = set()    # IDs de mensajes ya respondidos
        self._replied_comments = set()    # IDs de comentarios ya respondidos
        self._shared_posts = set()        # IDs de posts ya compartidos en historias
        print("✅ ModelFitBot inicializado correctamente")

    # ─── MENSAJES ─────────────────────────────────────────────────────────────

    def process_messages(self):
        print("\n📨 Revisando mensajes...")
        messages = self.api.get_unread_messages(limit=10)

        if not messages:
            print("  No hay mensajes nuevos")
            return

        for msg in messages:
            msg_id = msg["message_id"]
            sender_id = msg["sender_id"]

            if msg_id in self._replied_messages:
                continue

            # Si no hay texto ni imagen, saltar
            if not msg["text"] and not msg["has_image"]:
                continue

            print(f"\n  💬 Mensaje de {msg['from_name']}: {msg['text'][:60]}...")

            # Delay aleatorio humano antes de responder
            delay = random.randint(MSG_DELAY_MIN, MSG_DELAY_MAX)
            print(f"  ⏳ Esperando {delay}s para simular tiempo de respuesta...")
            _sleep(delay)

            # Marcar como leído
            self.api.mark_as_read(sender_id)

            # Obtener historial de conversación
            history = self.memory.get_conversation_history(sender_id, limit=6)

            # Generar respuesta
            if msg["has_image"]:
                print("  🖼️ Imagen detectada, usando visión...")
                response = self.gemini.generate_response_with_image(
                    image_url=msg["image_url"],
                    caption=msg["text"],
                    conversation_history=history
                )
            else:
                response = self.gemini.generate_response(
                    user_message=msg["text"],
                    conversation_history=history
                )

            # Simular que está escribiendo
            typing_time = random.randint(TYPING_MIN, TYPING_MAX)
            self.api.send_typing(sender_id)
            _sleep(typing_time)

            # Enviar respuesta
            sent = self.api.send_message(sender_id, response)

            if sent:
                # Guardar en memoria
                self.memory.add_interaction(
                    user_id=sender_id,
                    platform="facebook_message",
                    message=msg["text"] or "[imagen]",
                    response=response
                )
                self._replied_messages.add(msg_id)
                print(f"  ✅ Respondido: {response[:60]}...")

    # ─── COMENTARIOS ──────────────────────────────────────────────────────────

    def process_comments(self):
        print("\n💬 Revisando comentarios...")
        comments = self.api.get_recent_comments(post_limit=5)

        if not comments:
            print("  No hay comentarios nuevos")
            return

        new_comments = [c for c in comments if c["comment_id"] not in self._replied_comments]

        if not new_comments:
            print("  No hay comentarios nuevos sin responder")
            return

        print(f"  Encontrados {len(new_comments)} comentarios nuevos")

        for comment in new_comments:
            print(f"\n  💬 Comentario de {comment['commenter_name']}: {comment['text'][:60]}...")

            # Delay aleatorio
            delay = random.randint(COMMENT_DELAY_MIN, COMMENT_DELAY_MAX)
            print(f"  ⏳ Esperando {delay}s...")
            _sleep(delay)

            # Generar respuesta
            if comment["has_image"]:
                print("  🖼️ Imagen en comentario detectada...")
                response = self.gemini.generate_response_with_image(
                    image_url=comment["image_url"],
                    caption=comment["text"],
                )
            else:
                response = self.gemini.generate_comment_reply(
                    comment_text=comment["text"],
                    post_description=comment.get("post_message", "")
                )

            # Responder
            sent = self.api.reply_to_comment(comment["comment_id"], response)

            if sent:
                self.memory.add_interaction(
                    user_id=comment["commenter_id"],
                    platform="facebook_comment",
                    message=comment["text"] or "[imagen]",
                    response=response
                )
                self._replied_comments.add(comment["comment_id"])
                print(f"  ✅ Respondido: {response[:60]}...")

    # ─── HISTORIAS ────────────────────────────────────────────────────────────

    def process_stories(self):
        print("\n📸 Revisando publicaciones para compartir en historias...")
        posts = self.api.get_recent_posts(limit=3)

        if not posts:
            print("  No hay publicaciones recientes")
            return

        for post in posts:
            if post["post_id"] in self._shared_posts:
                continue

            if not post.get("image_url") and not post.get("message"):
                continue

            print(f"\n  📄 Post encontrado: {post['message'][:60]}...")

            # Generar caption atractivo con IA
            caption = self.gemini.generate_story_caption(post.get("message", "Nueva publicación"))
            print(f"  📝 Caption generado: {caption}")

            # Intentar compartir como historia
            shared = False

            if post.get("image_url"):
                shared = self.api.share_image_to_story(
                    image_url=post["image_url"],
                    caption=caption
                )

            if not shared:
                shared = self.api.share_post_to_story(
                    post_id=post["post_id"],
                    caption=caption
                )

            if shared:
                self._shared_posts.add(post["post_id"])
                print(f"  ✅ Post compartido en historias!")
            else:
                print(f"  ⚠️ No se pudo compartir en historias")

            # Solo compartir 1 post por ciclo para no saturar
            break

    # ─── CICLO PRINCIPAL ──────────────────────────────────────────────────────

    def run_cycle(self):
        self._cycle_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'='*50}")
        print(f"🔄 CICLO #{self._cycle_count} - {now}")
        print(f"{'='*50}")

        try:
            self.process_messages()
        except Exception as e:
            print(f"❌ Error en mensajes: {e}")

        try:
            self.process_comments()
        except Exception as e:
            print(f"❌ Error en comentarios: {e}")

        # Revisar historias cada N ciclos
        if self._cycle_count % STORY_CHECK_EVERY_N_CYCLES == 0:
            try:
                self.process_stories()
            except Exception as e:
                print(f"❌ Error en historias: {e}")

    def run_forever(self, interval_seconds: int = 300):
        """Loop infinito. Revisa mensajes y comentarios cada `interval_seconds` segundos."""
        print(f"\n🚀 Bot iniciado. Revisando cada {interval_seconds}s...")
        print("   Presiona Ctrl+C para detener\n")

        while True:
            try:
                self.run_cycle()
                print(f"\n💤 Durmiendo {interval_seconds}s hasta el próximo ciclo...")
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n👋 Bot detenido manualmente")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                print("   Reintentando en 60s...")
                time.sleep(60)

# src/modelfit_bot.py

import time
import random
import os
import json
from datetime import datetime, date
from src.meta_api import MetaAPI
from src.gemini_client import GeminiClient
from src.conversation_memory import ConversationMemory

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────

NO_DELAY = os.environ.get("BOT_NO_DELAY", "false").lower() == "true"

# Delays para mensajes y comentarios (segundos)
MSG_DELAY_MIN     = 60    # 1 minuto
MSG_DELAY_MAX     = 600   # 10 minutos
COMMENT_DELAY_MIN = 60    # 1 minuto
COMMENT_DELAY_MAX = 600   # 10 minutos
TYPING_MIN        = 3
TYPING_MAX        = 12

# Horario de silencio: el bot NO responde mensajes ni comentarios en este rango
SILENT_HOUR_START = 22   # 22:00
SILENT_HOUR_END   = 9    # 09:00

# Historias: cuántas publicar por día y en qué horario
STORIES_PER_DAY   = 10
# Horas del día en que se pueden publicar historias (fuera del silencio)
STORY_HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

# Archivo de persistencia para historias ya publicadas
STORIES_LOG_FILE = "database/stories_log.json"

# ─────────────────────────────────────────────────────────────────────────────


def _sleep(seconds: int):
    if NO_DELAY:
        print(f"  ⏩ Delay omitido ({seconds}s) — modo GitHub Actions")
        return
    time.sleep(seconds)


def _is_silent_hours() -> bool:
    """Devuelve True si estamos en el horario de silencio (22:00 - 09:00)."""
    hora = datetime.now().hour
    if SILENT_HOUR_START <= 23:
        # Rango cruza medianoche: 22..23 o 0..8
        return hora >= SILENT_HOUR_START or hora < SILENT_HOUR_END
    return False


def _load_stories_log() -> dict:
    """Carga el log de historias publicadas desde disco."""
    if os.path.exists(STORIES_LOG_FILE):
        try:
            with open(STORIES_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_stories_log(log: dict):
    """Guarda el log de historias publicadas en disco."""
    os.makedirs(os.path.dirname(STORIES_LOG_FILE), exist_ok=True)
    with open(STORIES_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


class ModelFitBot:
    def __init__(self):
        self.api    = MetaAPI()
        self.gemini = GeminiClient()
        self.memory = ConversationMemory()

        self._cycle_count      = 0
        self._replied_messages = set()
        self._replied_comments = set()

        # Log persistente: { "YYYY-MM-DD": ["post_id1", "post_id2", ...] }
        self._stories_log = _load_stories_log()

        print("✅ ModelFitBot inicializado correctamente")
        print(f"   Horario de silencio: {SILENT_HOUR_START}:00 → {SILENT_HOUR_END}:00")
        print(f"   Historias por día: {STORIES_PER_DAY}")

    # ─── HELPERS DE HISTORIAS ────────────────────────────────────────────────

    def _today_key(self) -> str:
        return date.today().isoformat()

    def _stories_today(self) -> list:
        return self._stories_log.get(self._today_key(), [])

    def _mark_story_published(self, post_id: str):
        key = self._today_key()
        if key not in self._stories_log:
            self._stories_log[key] = []
        self._stories_log[key].append(post_id)
        _save_stories_log(self._stories_log)

    def _already_shared_today(self, post_id: str) -> bool:
        return post_id in self._stories_today()

    def _all_ever_shared(self) -> set:
        """Todos los post_ids compartidos alguna vez (para no repetir en el día)."""
        all_ids = set()
        for ids in self._stories_log.values():
            all_ids.update(ids)
        return all_ids

    # ─── MENSAJES ─────────────────────────────────────────────────────────────

    def process_messages(self):
        if _is_silent_hours():
            print("\n🌙 Horario de silencio — no se responden mensajes")
            return

        print("\n📨 Revisando mensajes...")
        messages = self.api.get_unread_messages(limit=10)

        if not messages:
            print("  No hay mensajes nuevos")
            return

        for msg in messages:
            msg_id    = msg["message_id"]
            sender_id = msg["sender_id"]

            if msg_id in self._replied_messages:
                continue
            if not msg["text"] and not msg["has_image"]:
                continue

            print(f"\n  💬 Mensaje de {msg['from_name']}: {msg['text'][:60]}...")

            delay = random.randint(MSG_DELAY_MIN, MSG_DELAY_MAX)
            print(f"  ⏳ Esperando {delay}s antes de responder...")
            _sleep(delay)

            # Verificar silencio de nuevo tras el delay (pudo pasar la hora)
            if _is_silent_hours():
                print("  🌙 Entró en horario de silencio durante el delay, se responderá mañana")
                break

            self.api.mark_as_read(sender_id)
            history = self.memory.get_conversation_history(sender_id, limit=6)

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

            typing_time = random.randint(TYPING_MIN, TYPING_MAX)
            self.api.send_typing(sender_id)
            _sleep(typing_time)

            sent = self.api.send_message(sender_id, response)
            if sent:
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
        if _is_silent_hours():
            print("\n🌙 Horario de silencio — no se responden comentarios")
            return

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

            delay = random.randint(COMMENT_DELAY_MIN, COMMENT_DELAY_MAX)
            print(f"  ⏳ Esperando {delay}s...")
            _sleep(delay)

            if _is_silent_hours():
                print("  🌙 Entró en horario de silencio, comentarios restantes se responden mañana")
                break

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
        """
        Publica historias desde publicaciones antiguas de la página.
        - Máximo STORIES_PER_DAY historias al día
        - Solo publica en horas permitidas (fuera del silencio)
        - Selección aleatoria de posts (imágenes y reels)
        - Persiste en disco para no repetir durante el día
        """
        hora_actual = datetime.now().hour

        # No publicar historias en horario de silencio
        if hora_actual not in STORY_HOURS:
            print(f"\n📸 Historias: hora {hora_actual}:00 fuera del horario permitido, saltando...")
            return

        stories_hoy = self._stories_today()
        if len(stories_hoy) >= STORIES_PER_DAY:
            print(f"\n📸 Historias: ya se publicaron {STORIES_PER_DAY} historias hoy ✅")
            return

        restantes = STORIES_PER_DAY - len(stories_hoy)
        print(f"\n📸 Revisando historias... ({len(stories_hoy)}/{STORIES_PER_DAY} hoy, faltan {restantes})")

        # Obtener todos los posts disponibles
        all_posts = self.api.get_all_posts(limit=50)
        if not all_posts:
            print("  No hay posts disponibles")
            return

        # Filtrar los que ya se compartieron hoy
        ya_compartidos = self._all_ever_shared()
        disponibles = [p for p in all_posts if p["post_id"] not in ya_compartidos]

        # Si ya se usaron todos, permitir repetir (ciclo completo)
        if not disponibles:
            print("  ♻️ Todos los posts usados antes, reiniciando pool...")
            disponibles = all_posts

        # Mezclar aleatoriamente
        random.shuffle(disponibles)

        # Publicar 1 historia por ciclo (se distribuyen a lo largo del día)
        post = disponibles[0]
        print(f"\n  📄 Post seleccionado ({post['media_type']}): {post['message'][:60]}...")

        shared = self.api.share_post_to_story(post)

        if shared:
            self._mark_story_published(post["post_id"])
            total_hoy = len(self._stories_today())
            print(f"  ✅ Historia publicada! Total hoy: {total_hoy}/{STORIES_PER_DAY}")
        else:
            print(f"  ⚠️ No se pudo publicar la historia")

    # ─── CICLO PRINCIPAL ──────────────────────────────────────────────────────

    def run_cycle(self):
        self._cycle_count += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hora = datetime.now().hour
        en_silencio = _is_silent_hours()

        print(f"\n{'='*50}")
        print(f"🔄 CICLO #{self._cycle_count} — {now}")
        if en_silencio:
            print(f"🌙 MODO SILENCIO ({SILENT_HOUR_START}:00 - {SILENT_HOUR_END}:00)")
        print(f"{'='*50}")

        try:
            self.process_messages()
        except Exception as e:
            print(f"❌ Error en mensajes: {e}")

        try:
            self.process_comments()
        except Exception as e:
            print(f"❌ Error en comentarios: {e}")

        try:
            self.process_stories()
        except Exception as e:
            print(f"❌ Error en historias: {e}")

    def run_forever(self, interval_seconds: int = 300):
        """Loop infinito. Revisa todo cada `interval_seconds` segundos."""
        print(f"\n🚀 Bot iniciado. Revisando cada {interval_seconds//60} minutos...")
        print(f"   Silencio: {SILENT_HOUR_START}:00 → {SILENT_HOUR_END}:00")
        print(f"   Historias: {STORIES_PER_DAY}/día en horario {STORY_HOURS[0]}:00 - {STORY_HOURS[-1]}:00")
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

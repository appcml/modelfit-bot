# src/meta_api.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_API = "https://graph.facebook.com/v19.0"


class MetaAPI:
    def __init__(self):
        self.access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
        self.page_id = os.getenv("META_PAGE_ID")

        if not self.access_token or not self.page_id:
            raise ValueError("META_PAGE_ACCESS_TOKEN o META_PAGE_ID no configurados")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        params["access_token"] = self.access_token
        r = requests.get(f"{GRAPH_API}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, data: dict = None) -> dict:
        data = data or {}
        data["access_token"] = self.access_token
        r = requests.post(f"{GRAPH_API}/{endpoint}", json=data, timeout=15)
        r.raise_for_status()
        return r.json()

    # ─── MENSAJES ────────────────────────────────────────────────────────────

    def get_unread_messages(self, limit: int = 10) -> list:
        """Obtiene conversaciones recientes de la página."""
        try:
            data = self._get(
                f"{self.page_id}/conversations",
                {"fields": "participants,messages{message,from,attachments}", "limit": limit}
            )
            result = []
            for conv in data.get("data", []):
                msgs = conv.get("messages", {}).get("data", [])
                if not msgs:
                    continue
                last = msgs[0]
                participants = conv.get("participants", {}).get("data", [])
                sender = next((p for p in participants if p["id"] != self.page_id), None)
                if not sender:
                    continue

                # Detectar si hay adjunto (imagen)
                attachments = last.get("attachments", {}).get("data", [])
                image_url = None
                if attachments:
                    for att in attachments:
                        if att.get("image_data"):
                            image_url = att["image_data"].get("url")
                        elif att.get("file_url"):
                            image_url = att["file_url"]

                result.append({
                    "conversation_id": conv["id"],
                    "sender_id": sender["id"],
                    "from_name": sender.get("name", "Usuario"),
                    "text": last.get("message", ""),
                    "message_id": last["id"],
                    "image_url": image_url,
                    "has_image": image_url is not None,
                })
            return result
        except Exception as e:
            print(f"❌ Error get_unread_messages: {e}")
            return []

    def send_message(self, recipient_id: str, text: str) -> bool:
        """Envía un mensaje directo a un usuario."""
        try:
            self._post(
                f"{self.page_id}/messages",
                {
                    "recipient": {"id": recipient_id},
                    "message": {"text": text},
                    "messaging_type": "RESPONSE"
                }
            )
            print(f"  ✅ Mensaje enviado a {recipient_id}")
            return True
        except Exception as e:
            print(f"  ❌ Error send_message: {e}")
            return False

    def mark_as_read(self, recipient_id: str):
        """Marca la conversación como leída."""
        try:
            self._post(
                f"{self.page_id}/messages",
                {
                    "recipient": {"id": recipient_id},
                    "sender_action": "mark_seen"
                }
            )
        except Exception:
            pass

    def send_typing(self, recipient_id: str):
        """Simula que está escribiendo."""
        try:
            self._post(
                f"{self.page_id}/messages",
                {
                    "recipient": {"id": recipient_id},
                    "sender_action": "typing_on"
                }
            )
        except Exception:
            pass

    # ─── COMENTARIOS ─────────────────────────────────────────────────────────

    def get_recent_comments(self, post_limit: int = 5) -> list:
        """Obtiene comentarios recientes de las últimas publicaciones."""
        try:
            posts_data = self._get(
                f"{self.page_id}/posts",
                {"fields": "id,message,created_time", "limit": post_limit}
            )
            result = []
            for post in posts_data.get("data", []):
                comments_data = self._get(
                    f"{post['id']}/comments",
                    {"fields": "id,message,from,created_time,attachments", "limit": 20}
                )
                for comment in comments_data.get("data", []):
                    attachments = comment.get("attachments", {}).get("data", [])
                    image_url = None
                    if attachments:
                        for att in attachments:
                            if att.get("media", {}).get("image", {}).get("src"):
                                image_url = att["media"]["image"]["src"]

                    result.append({
                        "comment_id": comment["id"],
                        "post_id": post["id"],
                        "post_message": post.get("message", ""),
                        "commenter_id": comment.get("from", {}).get("id", ""),
                        "commenter_name": comment.get("from", {}).get("name", "Usuario"),
                        "text": comment.get("message", ""),
                        "image_url": image_url,
                        "has_image": image_url is not None,
                    })
            return result
        except Exception as e:
            print(f"❌ Error get_recent_comments: {e}")
            return []

    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        """Responde a un comentario."""
        try:
            self._post(
                f"{comment_id}/comments",
                {"message": text}
            )
            print(f"  ✅ Comentario respondido: {comment_id}")
            return True
        except Exception as e:
            print(f"  ❌ Error reply_to_comment: {e}")
            return False

    # ─── HISTORIAS ────────────────────────────────────────────────────────────

    def get_recent_posts(self, limit: int = 5) -> list:
        """Obtiene las publicaciones recientes de la página."""
        try:
            data = self._get(
                f"{self.page_id}/posts",
                {"fields": "id,message,full_picture,created_time,attachments", "limit": limit}
            )
            result = []
            for post in data.get("data", []):
                image_url = post.get("full_picture", "")

                # Intentar obtener imagen del primer adjunto si no hay full_picture
                if not image_url:
                    attachments = post.get("attachments", {}).get("data", [])
                    if attachments:
                        media = attachments[0].get("media", {})
                        image_url = media.get("image", {}).get("src", "")

                result.append({
                    "post_id": post["id"],
                    "message": post.get("message", ""),
                    "image_url": image_url,
                    "created_time": post.get("created_time", ""),
                })
            return result
        except Exception as e:
            print(f"❌ Error get_recent_posts: {e}")
            return []

    def share_post_to_story(self, post_id: str, caption: str = "") -> bool:
        """
        Comparte una publicación existente en las historias de Facebook.
        Requiere permiso: pages_manage_posts
        """
        try:
            # Método 1: Compartir directamente el post como historia con link
            page_url = f"https://www.facebook.com/{self.page_id}/posts/{post_id.split('_')[-1]}"

            # Crear historia con link a la publicación
            result = self._post(
                f"{self.page_id}/photo_stories",
                {
                    "link": page_url,
                    "message": caption,
                }
            )
            print(f"  ✅ Historia publicada: {result}")
            return True

        except Exception as e:
            print(f"  ⚠️ Método photo_stories falló, intentando con feed story: {e}")
            try:
                # Método 2: Publicar como historia desde imagen del post
                result = self._post(
                    f"{self.page_id}/stories",
                    {
                        "source_post_id": post_id,
                        "message": caption,
                    }
                )
                print(f"  ✅ Historia publicada (método 2): {result}")
                return True
            except Exception as e2:
                print(f"  ❌ Error share_post_to_story: {e2}")
                return False

    def share_image_to_story(self, image_url: str, caption: str = "") -> bool:
        """
        Publica una imagen como historia de Facebook.
        """
        try:
            result = self._post(
                f"{self.page_id}/photo_stories",
                {
                    "url": image_url,
                    "message": caption,
                }
            )
            print(f"  ✅ Historia con imagen publicada: {result}")
            return True
        except Exception as e:
            print(f"  ❌ Error share_image_to_story: {e}")
            return False

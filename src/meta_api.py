import requests
import time
from typing import Dict, List, Optional
import os

class MetaAPI:
    """Cliente para Facebook/Instagram Graph API."""
    
    def __init__(self):
        self.access_token = os.getenv('META_PAGE_ACCESS_TOKEN')
        self.page_id = os.getenv('META_PAGE_ID')
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.access_token or not self.page_id:
            raise ValueError("META_PAGE_ACCESS_TOKEN o META_PAGE_ID no configurados")
    
    def _make_request(self, endpoint: str, method: str = "GET", 
                     params: Dict = None, data: Dict = None) -> Dict:
        """Realiza petición a Graph API."""
        url = f"{self.base_url}/{endpoint}"
        
        default_params = {'access_token': self.access_token}
        if params:
            default_params.update(params)
        
        try:
            if method == "GET":
                response = requests.get(url, params=default_params, timeout=30)
            else:
                response = requests.post(url, params=default_params, 
                                       json=data, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error API Meta: {e}")
            return {'error': str(e)}
    
    def send_typing_indicator(self, recipient_id: str):
        """Envía indicador 'está escribiendo...'."""
        endpoint = f"me/messages"
        data = {
            'recipient': {'id': recipient_id},
            'sender_action': 'typing_on'
        }
        return self._make_request(endpoint, "POST", data=data)
    
    def send_message(self, recipient_id: str, text: str, 
                    delay_typing: float = None) -> bool:
        """
        Envía mensaje a usuario.
        
        Args:
            recipient_id: ID del usuario
            text: Texto a enviar
            delay_typing: Segundos de typing indicator antes de enviar
        """
        try:
            # Enviar typing indicator
            self.send_typing_indicator(recipient_id)
            
            # Simular delay de escritura
            if delay_typing:
                time.sleep(delay_typing)
            
            # Enviar mensaje
            endpoint = f"me/messages"
            data = {
                'recipient': {'id': recipient_id},
                'message': {'text': text}
            }
            
            result = self._make_request(endpoint, "POST", data=data)
            return 'error' not in result
            
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
            return False
    
    def get_unread_messages(self, limit: int = 20) -> List[Dict]:
        """
        Obtiene mensajes no leídos/conversaciones recientes.
        """
        # Obtener conversaciones de la página
        endpoint = f"{self.page_id}/conversations"
        params = {
            'fields': 'messages{from,message,created_time},unread_count',
            'limit': limit
        }
        
        result = self._make_request(endpoint, "GET", params=params)
        conversations = result.get('data', [])
        
        unread_messages = []
        for conv in conversations:
            if conv.get('unread_count', 0) > 0:
                messages = conv.get('messages', {}).get('data', [])
                for msg in messages:
                    # Solo mensajes entrantes (no de la página)
                    if msg.get('from', {}).get('id') != self.page_id:
                        unread_messages.append({
                            'id': msg.get('id'),
                            'from_id': msg.get('from', {}).get('id'),
                            'from_name': msg.get('from', {}).get('name'),
                            'text': msg.get('message'),
                            'created_time': msg.get('created_time'),
                            'conversation_id': conv.get('id')
                        })
        
        return unread_messages
    
    def get_recent_comments(self, post_limit: int = 10) -> List[Dict]:
        """
        Obtiene comentarios recientes en publicaciones.
        """
        # Primero obtener publicaciones recientes
        posts_endpoint = f"{self.page_id}/posts"
        posts_params = {
            'fields': 'id,message,created_time',
            'limit': post_limit
        }
        
        posts_result = self._make_request(posts_endpoint, "GET", params=posts_params)
        posts = posts_result.get('data', [])
        
        all_comments = []
        for post in posts:
            comments_endpoint = f"{post['id']}/comments"
            comments_params = {
                'fields': 'from,message,created_time,id',
                'limit': 50
            }
            
            comments_result = self._make_request(comments_endpoint, "GET", 
                                                params=comments_params)
            comments = comments_result.get('data', [])
            
            for comment in comments:
                # Ignorar comentarios de la página misma
                if comment.get('from', {}).get('id') != self.page_id:
                    all_comments.append({
                        'id': comment.get('id'),
                        'post_id': post.get('id'),
                        'from_id': comment.get('from', {}).get('id'),
                        'from_name': comment.get('from', {}).get('name'),
                        'text': comment.get('message'),
                        'created_time': comment.get('created_time')
                    })
        
        return all_comments
    
    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        """Responde a un comentario."""
        try:
            endpoint = f"{comment_id}/comments"
            data = {'message': text}
            
            result = self._make_request(endpoint, "POST", data=data)
            return 'error' not in result
            
        except Exception as e:
            print(f"Error respondiendo comentario: {e}")
            return False
    
    def mark_as_read(self, conversation_id: str) -> bool:
        """Marca conversación como leída."""
        try:
            endpoint = f"{conversation_id}"
            data = {'unread_count': 0}
            
            result = self._make_request(endpoint, "POST", data=data)
            return 'error' not in result
            
        except Exception as e:
            print(f"Error marcando como leído: {e}")
            return False

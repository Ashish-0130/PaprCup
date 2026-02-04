from typing import Dict, List, Optional
from .utils import calculate_haversine_distance

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, dict] = {}
        self.queue: List[str] = []
        self.rooms: Dict[str, str] = {}

    async def connect(self, sid: str, data: dict):
        self.active_connections[sid] = data

    def disconnect(self, sid: str):
        if sid in self.active_connections:
            del self.active_connections[sid]
        if sid in self.queue:
            self.queue.remove(sid)
        if sid in self.rooms:
            del self.rooms[sid]

    def assign_room(self, sid: str, room_id: str):
        self.rooms[sid] = room_id
        # CRITICAL FIX: Ensure they are removed from queue so they don't match twice
        if sid in self.queue:
            self.queue.remove(sid)

    def get_room(self, sid: str) -> Optional[str]:
        return self.rooms.get(sid)

    def get_user(self, sid: str) -> dict:
        return self.active_connections.get(sid, {})

    def cleanup_room(self, room_id: str):
        """Remove room association for all users in this room"""
        users_to_remove = [k for k, v in self.rooms.items() if v == room_id]
        for u in users_to_remove:
            del self.rooms[u]

    def find_match(self, sid: str) -> Optional[str]:
        me = self.active_connections.get(sid)
        if not me: return None

        # Loop through a COPY of the queue
        for candidate_sid in list(self.queue):
            if candidate_sid == sid: continue 
            
            candidate = self.active_connections.get(candidate_sid)
            if not candidate:
                self.queue.remove(candidate_sid)
                continue

            # 1. Gender Logic
            if me['looking_for'] != 'any' and me['looking_for'] != candidate['gender']:
                continue
            if candidate['looking_for'] != 'any' and candidate['looking_for'] != me['gender']:
                continue

            # 2. Match Found
            self.queue.remove(candidate_sid) # Remove candidate from queue
            if sid in self.queue:
                self.queue.remove(sid)   # Remove self from queue
                
            return candidate_sid

        # No match found, add self to queue
        if sid not in self.queue:
            self.queue.append(sid)
            
        return None

manager = ConnectionManager()
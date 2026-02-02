from typing import Dict, List, Optional
from .utils import calculate_haversine_distance

class ConnectionManager:
    def __init__(self):
        # Stores active user metadata: {'sid': {'bio': '...', 'gender': '...'}}
        self.active_connections: Dict[str, dict] = {}
        
        # The Waiting Queue (List of SIDs)
        self.queue: List[str] = []
        
        # Maps SID -> RoomID
        self.rooms: Dict[str, str] = {}

    async def connect(self, sid: str, data: dict):
        """Register user data."""
        self.active_connections[sid] = data

    def disconnect(self, sid: str):
        """Remove user from all state stores."""
        if sid in self.active_connections:
            del self.active_connections[sid]
        if sid in self.queue:
            self.queue.remove(sid)
        if sid in self.rooms:
            del self.rooms[sid]

    def assign_room(self, sid: str, room_id: str):
        self.rooms[sid] = room_id

    def get_room(self, sid: str) -> Optional[str]:
        return self.rooms.get(sid)

    def get_user(self, sid: str) -> dict:
        return self.active_connections.get(sid, {})

    def find_match(self, sid: str) -> Optional[str]:
        """
        Scans the queue for a compatible partner.
        Returns Partner SID if found, else None.
        """
        me = self.active_connections.get(sid)
        if not me: return None

        # Iterate over a copy of the queue to safely modify if needed
        for candidate_sid in list(self.queue):
            if candidate_sid == sid: continue # Skip self
            
            candidate = self.active_connections.get(candidate_sid)
            if not candidate:
                self.queue.remove(candidate_sid) # Clean dead link
                continue

            # --- FILTER LOGIC ---
            
            # 1. Gender Compatibility
            # If I want specific gender, and candidate isn't it -> Skip
            if me['looking_for'] != 'any' and me['looking_for'] != candidate['gender']:
                continue
            
            # If Candidate wants specific gender, and I am not it -> Skip
            if candidate['looking_for'] != 'any' and candidate['looking_for'] != me['gender']:
                continue

            # 2. Proximity (Optional)
            # Only checked if CURRENT user requested it AND both have GPS data
            if me['is_premium'] and me['lat'] and candidate['lat']:
                dist = calculate_haversine_distance(
                    me['lat'], me['lon'],
                    candidate['lat'], candidate['lon']
                )
                # If too far (e.g., > 100km), skip
                if dist > 100.0:
                    continue

            # --- MATCH SUCCESS ---
            self.queue.remove(candidate_sid)
            return candidate_sid

        # No match found, add self to waiting queue
        if sid not in self.queue:
            self.queue.append(sid)
            
        return None

# Singleton Instance
manager = ConnectionManager()
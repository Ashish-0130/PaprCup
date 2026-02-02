from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import socketio
from app.manager import manager
from app.utils import sanitize_message

# Initialize FastAPI App
app = FastAPI(docs_url=None, redoc_url=None) # Hide docs for production

# Setup Template Engine (Jinja2) and Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Async Socket.IO Server
# CORS set to '*' allows connections from any domain (useful for dev/testing)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# --- HTTP Routes ---

@app.get("/")
async def get_home(request: Request):
    """Serves the main SPA (Single Page Application) HTML."""
    return templates.TemplateResponse("index.html", {"request": request})

# --- WebSocket Events ---

@sio.event
async def connect(sid, environ):
    """
    Called when a client connects via WebSocket.
    Note: Real logic happens in 'join_queue' when we have user data.
    """
    pass

@sio.event
async def join_queue(sid, data):
    """
    User clicks 'Start Talking'. 
    We validate their data and try to find a match.
    """
    # 1. Sanitize Inputs (Security)
    clean_bio = sanitize_message(data.get('bio', ''))[:50] # Limit to 50 chars
    
    # 2. Store User Data
    user_data = {
        "bio": clean_bio,
        "gender": data.get("gender", "any"),
        "looking_for": data.get("looking_for", "any"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "is_premium": bool(data.get("is_premium", False))
    }
    await manager.connect(sid, user_data)
    
    # 3. Attempt Matchmaking
    match_sid = manager.find_match(sid)
    
    if match_sid:
        # Match Found! Create a unique room.
        room_id = f"{sid}_{match_sid}"
        
        # Link both users to this room
        manager.assign_room(sid, room_id)
        manager.assign_room(match_sid, room_id)
        
        # Move sockets into the room
        await sio.enter_room(sid, room_id)
        await sio.enter_room(match_sid, room_id)
        
        # Notify both users (Exchange Bios)
        p1 = manager.get_user(sid)
        p2 = manager.get_user(match_sid)
        
        await sio.emit('match_found', {'bio': p2['bio']}, room=sid)
        await sio.emit('match_found', {'bio': p1['bio']}, room=match_sid)
    else:
        # No match yet, tell client to wait
        await sio.emit('waiting', {}, room=sid)

@sio.event
async def send_message(sid, data):
    """
    Relays a chat message to the partner in the room.
    """
    room_id = manager.get_room(sid)
    if room_id:
        # Sanitize text content before relaying
        if data.get('type') == 'text':
            data['content'] = sanitize_message(data.get('content', ''))
            
        # Send to everyone in room EXCEPT sender (skip_sid)
        await sio.emit('receive_message', data, room=room_id, skip_sid=sid)

@sio.event
async def skip_partner(sid):
    """
    User clicked 'Next'. We notify the partner and clean up room state.
    """
    room_id = manager.get_room(sid)
    if room_id:
        await sio.emit('partner_left', {}, room=room_id)
        # Note: We don't disconnect sockets here, just logic.
        # The client will re-emit 'join_queue' automatically.

@sio.event
async def disconnect(sid):
    """
    User closed tab or lost connection.
    """
    room_id = manager.get_room(sid)
    if room_id:
        await sio.emit('partner_left', {}, room=room_id)
    
    # Clean up all memory references
    manager.disconnect(sid)

# Entry point for local debugging
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
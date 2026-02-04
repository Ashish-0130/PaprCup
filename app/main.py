import os
import socketio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.manager import manager
from app.utils import sanitize_message

# 1. Setup Paths (Fixes file not found errors)
# This gets the root folder of your project dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 2. Initialize FastAPI
fastapi_app = FastAPI(docs_url=None, redoc_url=None)

# 3. Mount Assets
templates = Jinja2Templates(directory=TEMPLATE_DIR)
fastapi_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 4. Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        "https://paprcup.onrender.com",
        "http://paprcup.onrender.com",
        "*" 
    ],
    logger=True,
    engineio_logger=True
)

# 5. Wrap FastAPI
app = socketio.ASGIApp(sio, fastapi_app)

# --- HTTP Routes ---

@fastapi_app.get("/")
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- WebSocket Events ---

@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")

@sio.event
async def join_queue(sid, data):
    print(f"📝 User {sid} joining queue. Prefs: {data.get('looking_for')}")
    
    clean_bio = sanitize_message(data.get('bio', ''))[:50]
    
    user_data = {
        "bio": clean_bio,
        "gender": data.get("gender", "any"),
        "looking_for": data.get("looking_for", "any"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "is_premium": bool(data.get("is_premium", False))
    }
    
    await manager.connect(sid, user_data)
    
    # Try to find a match
    match_sid = manager.find_match(sid)
    
    if match_sid:
        print(f"🎉 MATCH FOUND: {sid} <--> {match_sid}")
        
        room_id = f"room_{sid[:4]}_{match_sid[:4]}"
        
        # Critical: Assign rooms and update state
        manager.assign_room(sid, room_id)
        manager.assign_room(match_sid, room_id)
        
        # Socket.IO Join
        await sio.enter_room(sid, room_id)
        await sio.enter_room(match_sid, room_id)
        
        p1 = manager.get_user(sid)
        p2 = manager.get_user(match_sid)
        
        await sio.emit('match_found', {'bio': p2.get('bio', 'Stranger')}, room=sid)
        await sio.emit('match_found', {'bio': p1.get('bio', 'Stranger')}, room=match_sid)
    else:
        print(f"⏳ No match yet for {sid}. Added to queue.")
        await sio.emit('waiting', {}, room=sid)

@sio.event
async def send_message(sid, data):
    room_id = manager.get_room(sid)
    if room_id:
        if data.get('type') == 'text':
            data['content'] = sanitize_message(data.get('content', ''))
        await sio.emit('receive_message', data, room=room_id, skip_sid=sid)

@sio.event
async def skip_partner(sid):
    print(f"🚫 User {sid} skipped partner")
    room_id = manager.get_room(sid)
    if room_id:
        await sio.emit('partner_left', {}, room=room_id, skip_sid=sid)
        manager.cleanup_room(room_id)

@sio.event
async def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")
    room_id = manager.get_room(sid)
    if room_id:
        await sio.emit('partner_left', {}, room=room_id)
    manager.disconnect(sid)
/* socket_client.js */

// 1. Initialize Socket
// passing no URL allows it to auto-detect domain (Render or Localhost)
const socket = io({
    transports: ['websocket', 'polling'], // Force stable transport
    reconnection: true
});

// --- STATE ---
let myLocation = { lat: null, lon: null };

// --- SOCKET EVENTS ---

socket.on('connect', () => {
    console.log("Connected to server:", socket.id);
    window.UI.updateStatus("Live");
});

socket.on('connect_error', (err) => {
    console.error("Connection failed:", err);
    window.UI.updateStatus("Offline", "red");
});

// 1. Waiting for partner
socket.on('waiting', () => {
    window.UI.showView('searching');
});

// 2. Match Found
socket.on('match_found', (data) => {
    window.UI.setPartnerProfile(data.bio);
    window.UI.clearChat();
    window.UI.showView('chat');
});

// 3. Receive Message
socket.on('receive_message', (data) => {
    window.UI.appendMessage(data, false);
});

// 4. Partner Left
socket.on('partner_left', () => {
    window.UI.appendSystemMessage("Partner has disconnected.");
    // Optional: Auto-skip after 2 seconds or let user click 'Next'
});

// --- USER ACTIONS ---

// A. Setup Form Submission
document.getElementById('setup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI Feedback
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = "Accessing GPS...";
    
    const gender = document.getElementById('gender').value;
    const lookingFor = document.getElementById('looking_for').value;
    const bio = document.getElementById('bio').value;
    const isPremium = document.getElementById('premium-toggle').checked;

    // Optional GPS Logic
    if (isPremium && navigator.geolocation) {
        try {
            const pos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
            });
            myLocation = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        } catch (err) {
            console.log("GPS denied or failed, proceeding without location.");
        }
    }

    // Join Queue
    btn.innerText = originalText;
    window.UI.showView('searching');
    
    socket.emit('join_queue', {
        bio: bio,
        gender: gender,
        looking_for: lookingFor,
        is_premium: isPremium,
        lat: myLocation.lat,
        lon: myLocation.lon
    });
});

// B. Send Text Message
document.getElementById('btn-send').addEventListener('click', sendMessage);
document.getElementById('msg-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
    const input = window.UI.elements.msgInput;
    const content = input.value.trim();
    
    if (content) {
        // 1. Emit to server
        socket.emit('send_message', { type: 'text', content: content });
        
        // 2. Show in own chat immediately (optimistic UI)
        window.UI.appendMessage({ type: 'text', content: content }, true);
        
        // 3. Clear input
        input.value = '';
    }
}

// C. Skip Partner
document.getElementById('btn-skip').addEventListener('click', () => {
    socket.emit('skip_partner');
    window.UI.showView('searching');
    
    // Re-join queue automatically with previous settings? 
    // For now, we force them to click "Start" again or just emit join_queue again.
    // Let's loop them back to searching:
    const gender = document.getElementById('gender').value;
    const lookingFor = document.getElementById('looking_for').value;
    const bio = document.getElementById('bio').value;
    
    socket.emit('join_queue', {
        bio: bio,
        gender: gender,
        looking_for: lookingFor,
        lat: myLocation.lat,
        lon: myLocation.lon
    });
});

// D. Image Upload
const fileInput = document.getElementById('img-input');
fileInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(evt) {
            const base64 = evt.target.result;
            socket.emit('send_message', { type: 'image', content: base64 });
            window.UI.appendMessage({ type: 'image', content: base64 }, true);
        };
        reader.readAsDataURL(file);
    }
    // Reset input so same file can be selected again
    this.value = '';
});
/**
 * Socket Client Logic
 */

// Initialize Socket.IO (No connection yet)
const socket = io({
    autoConnect: false,
    transports: ['websocket'],
    reconnectionAttempts: 5
});

// Store user preferences globally for re-queueing
let userSettings = {};

// --- 1. START TALKING (Form Submission) ---
document.getElementById('setup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Harvest Data from DOM
    const bioInput = document.getElementById('bio').value.trim();
    
    userSettings = {
        gender: document.getElementById('gender').value,
        looking_for: document.getElementById('looking_for').value,
        bio: bioInput || "Just saying hi 👋", // Default bio
        is_premium: document.getElementById('premium-toggle').checked,
        lat: null,
        lon: null
    };

    // Handle Optional Geolocation
    if (userSettings.is_premium && "geolocation" in navigator) {
        try {
            // Request location with 4s timeout
            const pos = await new Promise((resolve, reject) => 
                navigator.geolocation.getCurrentPosition(resolve, reject, {timeout: 4000})
            );
            userSettings.lat = pos.coords.latitude;
            userSettings.lon = pos.coords.longitude;
        } catch (err) {
            console.log("Geo access denied or timed out. Proceeding without location.");
        }
    }

    // Connect and Search
    socket.connect();
    UI.switchView('searching');
    socket.emit('join_queue', userSettings);
});

// --- 2. SENDING MESSAGES ---

// Send via Button
document.getElementById('btn-send').addEventListener('click', sendText);

// Send via Enter Key
document.getElementById('msg-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendText();
});

function sendText() {
    const input = document.getElementById('msg-input');
    const msg = input.value.trim();
    if (!msg) return;

    // Emit to server
    socket.emit('send_message', { type: 'text', content: msg });
    
    // Show locally immediately (Optimistic UI)
    UI.appendMessage('text', msg, true);
    input.value = ''; // Clear input
    input.focus();
}

// Image Upload Handling
document.getElementById('img-input').addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        // Limit size to 2MB to prevent socket crash
        if (file.size > 2 * 1024 * 1024) {
            alert("Image is too large. Please send an image under 2MB.");
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const base64 = e.target.result;
            socket.emit('send_message', { type: 'image', content: base64 });
            UI.appendMessage('image', base64, true);
        };
        reader.readAsDataURL(file);
    }
    this.value = ''; // Reset file input
});

// --- 3. SKIPPING / NEXT PARTNER ---
document.getElementById('btn-skip').addEventListener('click', () => {
    socket.emit('skip_partner'); // Notify server to disconnect logic
    UI.resetChat();
    UI.switchView('searching');
    
    // Artificial delay (500ms) to make the "Search" feel real
    setTimeout(() => {
        socket.emit('join_queue', userSettings);
    }, 500);
});

// --- 4. SOCKET EVENT LISTENERS ---

// Server found a match
socket.on('match_found', (data) => {
    UI.switchView('chat');
    UI.partnerBio.textContent = data.bio || "Stranger";
    UI.appendSystemMessage("You are now connected.");
});

// Received a message
socket.on('receive_message', (data) => {
    UI.appendMessage(data.type, data.content, false);
});

// Partner left the chat
socket.on('partner_left', () => {
    UI.appendSystemMessage("Partner disconnected.");
    UI.appendSystemMessage("Searching for a new match...");
    
    // Auto Re-queue after 2 seconds
    setTimeout(() => {
        socket.emit('join_queue', userSettings);
        UI.resetChat(); // Clear the "Partner disconnected" msg
        UI.switchView('searching');
    }, 2000);
});
/**
 * UI Controller
 * Handles view transitions and message rendering.
 */
const UI = {
    // Cache DOM elements for performance
    views: {
        setup: document.getElementById('view-setup'),
        searching: document.getElementById('view-searching'),
        chat: document.getElementById('view-chat')
    },
    chatFeed: document.getElementById('chat-feed'),
    partnerBio: document.getElementById('partner-bio'),

    /**
     * Switches the visible screen (Setup -> Search -> Chat)
     */
    switchView(viewName) {
        // Hide all views first
        Object.values(this.views).forEach(el => el.classList.add('hidden'));
        
        // Show target view
        const target = this.views[viewName];
        target.classList.remove('hidden');
        
        // Scroll to top of new view
        window.scrollTo(0, 0);
    },

    /**
     * Renders a message bubble in the chat feed
     * @param {string} type - 'text' or 'image'
     * @param {string} content - The text or base64 image data
     * @param {boolean} isMe - True if sent by local user
     */
    appendMessage(type, content, isMe) {
        const div = document.createElement('div');
        div.className = `msg ${isMe ? 'me' : 'them'}`;
        
        if (type === 'text') {
            // Securely set text to prevent XSS
            div.textContent = content; 
        } else if (type === 'image') {
            // Render Image
            div.className += ' img-msg';
            div.innerHTML = `<img src="${content}" style="max-width:100%; border-radius:12px; display:block;">`;
        }

        this.chatFeed.appendChild(div);
        this.scrollToBottom();
    },

    /**
     * Renders a grey system notification (e.g. "Partner disconnected")
     */
    appendSystemMessage(text) {
        const div = document.createElement('div');
        div.className = 'system-message';
        div.textContent = text;
        this.chatFeed.appendChild(div);
        this.scrollToBottom();
    },

    /**
     * Clears chat history (for next match)
     */
    resetChat() {
        this.chatFeed.innerHTML = '';
        this.appendSystemMessage("Connecting to a new partner...");
    },

    /**
     * Smooth scroll to latest message
     */
    scrollToBottom() {
        this.chatFeed.scrollTop = this.chatFeed.scrollHeight;
    }
};
(function() {
    // Configuration
    const API_URL = 'http://localhost:8000'; // Update this to your production backend URL
    const ACCENT_COLOR = '#3b82f6';
    const BOT_NAME = 'Beatriz';
    const INITIAL_MESSAGE = 'Olá! Sou a Beatriz, assistente virtual do Hugo Galaz. Para o encaminhar da melhor forma, diga-me: qual é o principal bloqueio tecnológico ou operacional que a sua empresa enfrenta hoje?';

    // Create and inject Tailwind CSS if not present
    if (!document.getElementById('tailwind-cdn')) {
        const script = document.createElement('script');
        script.id = 'tailwind-cdn';
        script.src = 'https://cdn.tailwindcss.com';
        document.head.appendChild(script);
    }

    // Styles for the widget
    const style = document.createElement('style');
    style.innerHTML = `
        #beatriz-chat-widget {
            z-index: 9999;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
        }
        #beatriz-chat-window {
            display: none;
            flex-direction: column;
            width: 380px;
            max-width: 90vw;
            height: 500px;
            max-height: 80vh;
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
            position: fixed;
            bottom: 85px;
            right: 20px;
            overflow: hidden;
            transition: all 0.3s ease-in-out;
        }
        #beatriz-chat-window.open {
            display: flex;
        }
        #beatriz-messages {
            flex-grow: 1;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #374151 #111827;
        }
        #beatriz-messages::-webkit-scrollbar {
            width: 6px;
        }
        #beatriz-messages::-webkit-scrollbar-track {
            background: #111827;
        }
        #beatriz-messages::-webkit-scrollbar-thumb {
            background-color: #374151;
            border-radius: 10px;
        }
        .typing-indicator span {
            display: inline-block;
            width: 4px;
            height: 4px;
            background-color: #9ca3af;
            border-radius: 50%;
            margin: 0 1px;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }
        #mic-btn.recording {
            animation: pulse 1.5s infinite;
            color: #ef4444;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
    `;
    document.head.appendChild(style);

    // Create Widget Container
    const widget = document.createElement('div');
    widget.id = 'beatriz-chat-widget';
    widget.innerHTML = `
        <div id="beatriz-chat-window" class="flex flex-col">
            <!-- Header -->
            <div class="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">B</div>
                    <div>
                        <h3 class="text-white text-sm font-semibold">${BOT_NAME}</h3>
                        <p class="text-gray-400 text-xs flex items-center">
                            <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span> Online
                        </p>
                    </div>
                </div>
                <button id="close-chat" class="text-gray-400 hover:text-white transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Messages -->
            <div id="beatriz-messages" class="p-4 space-y-4 bg-gray-950">
                <!-- Messages will be injected here -->
            </div>

            <!-- Input -->
            <div class="p-4 border-t border-gray-800 bg-gray-900">
                <form id="beatriz-form" class="flex items-center space-x-2">
                    <button type="button" id="mic-btn" class="p-2 text-gray-400 hover:text-blue-500 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </button>
                    <input type="text" id="beatriz-input"
                        class="flex-grow bg-gray-800 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 border-gray-700 outline-none"
                        placeholder="Escreva uma mensagem..." required>
                    <button type="submit" class="p-2.5 text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-800 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </form>
            </div>
            <audio id="beatriz-audio" class="hidden"></audio>
        </div>

        <!-- Floating Button -->
        <button id="beatriz-toggle" class="fixed bottom-5 right-5 w-14 h-14 bg-blue-600 rounded-full shadow-lg flex items-center justify-center text-white hover:bg-blue-700 transition-all transform hover:scale-110 active:scale-95 z-[10000]">
            <svg id="chat-icon" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
        </button>
    `;
    document.body.appendChild(widget);

    // Chat Logic
    const toggleBtn = document.getElementById('beatriz-toggle');
    const closeBtn = document.getElementById('close-chat');
    const chatWindow = document.getElementById('beatriz-chat-window');
    const messageContainer = document.getElementById('beatriz-messages');
    const chatForm = document.getElementById('beatriz-form');
    const chatInput = document.getElementById('beatriz-input');
    const micBtn = document.getElementById('mic-btn');
    const audioPlayer = document.getElementById('beatriz-audio');

    let history = JSON.parse(sessionStorage.getItem('beatriz_history')) || [];
    let recognition = null;

    // Speech Recognition Setup
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'pt-PT';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            micBtn.classList.add('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            micBtn.classList.remove('recording');
        };

        recognition.onend = () => {
            micBtn.classList.remove('recording');
        };

        micBtn.onclick = () => {
            if (micBtn.classList.contains('recording')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        };
    } else {
        micBtn.style.display = 'none';
    }

    function toggleChat() {
        chatWindow.classList.toggle('open');
    }

    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    function addMessage(text, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = `max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
            role === 'user'
                ? 'bg-blue-600 text-white rounded-tr-none'
                : 'bg-gray-800 text-gray-200 rounded-tl-none border border-gray-700'
        }`;

        // Handle links in text
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const htmlText = text.replace(urlRegex, function(url) {
            return `<a href="${url}" target="_blank" class="underline decoration-blue-400 text-blue-300 font-medium">${url}</a>`;
        });

        contentDiv.innerHTML = htmlText;
        msgDiv.appendChild(contentDiv);
        messageContainer.appendChild(msgDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'beatriz-typing';
        typingDiv.className = 'flex justify-start';
        typingDiv.innerHTML = `
            <div class="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-none px-4 py-3 flex items-center">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messageContainer.appendChild(typingDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    function removeTyping() {
        const typingDiv = document.getElementById('beatriz-typing');
        if (typingDiv) typingDiv.remove();
    }

    function playAudio(base64Audio) {
        if (!base64Audio) return;
        audioPlayer.src = `data:audio/mpeg;base64,${base64Audio}`;
        audioPlayer.play().catch(e => console.error('Audio playback failed', e));
    }

    // Initialize Chat
    if (history.length === 0) {
        addMessage(INITIAL_MESSAGE, 'model');
        history.push({ role: 'model', parts: INITIAL_MESSAGE });
        sessionStorage.setItem('beatriz_history', JSON.stringify(history));
    } else {
        history.forEach(msg => {
            if (msg.role === 'user') {
                addMessage(msg.parts, 'user');
            } else if (msg.role === 'model') {
                addMessage(msg.parts, 'model');
            }
        });
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        chatInput.value = '';
        addMessage(message, 'user');
        showTyping();

        try {
            const response = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, history: history })
            });

            const data = await response.json();
            removeTyping();

            if (data.response) {
                addMessage(data.response, 'model');
                history = data.history;
                sessionStorage.setItem('beatriz_history', JSON.stringify(history));

                if (data.audio_base64) {
                    playAudio(data.audio_base64);
                }
            } else {
                addMessage('Desculpe, ocorreu um erro ao processar o seu pedido.', 'model');
            }
        } catch (error) {
            console.error('Beatriz Chat Error:', error);
            removeTyping();
            addMessage('Não consegui ligar ao servidor. Por favor, tente mais tarde.', 'model');
        }
    });
})();

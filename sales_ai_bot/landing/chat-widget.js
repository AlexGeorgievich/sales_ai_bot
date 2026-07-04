// Sales AI Widget
(function() {
    'use strict';
    
    const config = window.SalesAIConfig || {};
    const theme = config.theme || {};
    const texts = config.texts || {};
    const behavior = config.behavior || {};
    
    let sessionId = null;
    let clientType = config.defaultClientType || 'msb';
    let isOpen = false;
    
    // Инициализация виджета
    function init() {
        createWidget();
        attachEventListeners();
        
        if (behavior.autoOpen) {
            setTimeout(() => toggleChat(), 1000);
        }
        
        // Генерируем уникальный session ID
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        console.log('Sales AI Widget initialized', { sessionId, clientType });
    }
    
    // Создание DOM элементов
    function createWidget() {
        const container = document.getElementById('sales-ai-widget');
        
        container.innerHTML = `
            <button class="sales-ai-toggle-btn" id="sales-ai-toggle">
                <svg viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 1 4.29L2 22l5.71-1C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.38 0-2.67-.33-3.82-.91l-.27-.15-2.86.5.51-2.86-.15-.27C4.33 14.67 4 13.38 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8z"/>
                    <circle cx="9" cy="12" r="1"/>
                    <circle cx="12" cy="12" r="1"/>
                    <circle cx="15" cy="12" r="1"/>
                </svg>
            </button>
            
            <div class="sales-ai-chat-container" id="sales-ai-chat">
                <div class="sales-ai-header">
                    <div class="sales-ai-avatar">🤖</div>
                    <div class="sales-ai-header-info">
                        <h3>AI Ассистент</h3>
                        <p>Онлайн • Отвечаем за 2 секунды</p>
                    </div>
                    <button class="sales-ai-close-btn" id="sales-ai-close">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>
                
                <div class="sales-ai-messages" id="sales-ai-messages">
                    <div class="sales-ai-message bot">
                        <div class="sales-ai-message-bubble">
                            ${texts.welcomeMessage || 'Здравствуйте! Я AI-ассистент отдела продаж. Чем могу помочь?'}
                        </div>
                    </div>
                </div>
                
                <div class="sales-ai-input-container">
                    <input 
                        type="text" 
                        class="sales-ai-input" 
                        id="sales-ai-input" 
                        placeholder="${texts.placeholder || 'Напишите ваш вопрос...'}"
                        autocomplete="off"
                    >
                    <button class="sales-ai-send-btn" id="sales-ai-send">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        // Подключаем стили
        const styleLink = document.createElement('link');
        styleLink.rel = 'stylesheet';
        styleLink.href = 'chat-widget.css';
        document.head.appendChild(styleLink);
    }
    
    // Привязка событий
    function attachEventListeners() {
        document.getElementById('sales-ai-toggle').addEventListener('click', toggleChat);
        document.getElementById('sales-ai-close').addEventListener('click', toggleChat);
        document.getElementById('sales-ai-send').addEventListener('click', sendMessage);
        document.getElementById('sales-ai-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
    
    // Открытие/закрытие чата
    function toggleChat() {
        const chat = document.getElementById('sales-ai-chat');
        isOpen = !isOpen;
        
        if (isOpen) {
            chat.classList.add('open');
            document.getElementById('sales-ai-input').focus();
        } else {
            chat.classList.remove('open');
            resetSession();
        }
    }
    
    // Сброс текущей сессии
    function resetSession() {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const messagesContainer = document.getElementById('sales-ai-messages');
        messagesContainer.innerHTML = `
            <div class="sales-ai-message bot">
                <div class="sales-ai-message-bubble">
                    \${texts.welcomeMessage || 'Здравствуйте! Я AI-ассистент отдела продаж. Чем могу помочь?'}
                </div>
            </div>
        `;
        console.log('Session reset, new sessionId generated:', sessionId);
    }
    
    // Отправка сообщения
    async function sendMessage() {
        const input = document.getElementById('sales-ai-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Добавляем сообщение пользователя
        addMessage(message, 'user');
        input.value = '';
        
        // Показываем индикатор загрузки
        showTypingIndicator();
        
        try {
            // Отправляем запрос к API
            const rawApiUrl = config.apiUrl || 'http://localhost:8000';
            const cleanApiUrl = rawApiUrl.replace(/\/$/, "");
            const response = await fetch(`${cleanApiUrl}/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: sessionId,
                    message: message,
                    client_type: clientType,
                    session_id: sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error('API error');
            }
            
            const data = await response.json();
            
            // Убираем индикатор загрузки
            hideTypingIndicator();
            
            // Добавляем ответ бота
            addMessage(data.response, 'bot');
            
        } catch (error) {
            console.error('Error sending message:', error);
            hideTypingIndicator();
            addMessage(texts.error || 'Извините, произошла ошибка. Попробуйте позже.', 'bot');
        }
    }
    
    // Добавление сообщения в чат
    function addMessage(text, sender) {
        const messagesContainer = document.getElementById('sales-ai-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `sales-ai-message ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'sales-ai-message-bubble';
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        
        // Прокрутка вниз
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Индикатор загрузки
    function showTypingIndicator() {
        const messagesContainer = document.getElementById('sales-ai-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'sales-ai-message bot';
        typingDiv.id = 'sales-ai-typing';
        
        typingDiv.innerHTML = `
            <div class="sales-ai-message-bubble">
                <div class="sales-ai-typing">
                    <div class="sales-ai-typing-dot"></div>
                    <div class="sales-ai-typing-dot"></div>
                    <div class="sales-ai-typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function hideTypingIndicator() {
        const typing = document.getElementById('sales-ai-typing');
        if (typing) typing.remove();
    }
    
    // Публичные методы
    window.SalesAIWidget = {
        setClientType: function(type) {
            clientType = type;
            console.log('Client type set to:', type);
        },
        
        open: function() {
            if (!isOpen) toggleChat();
        },
        
        close: function() {
            if (isOpen) toggleChat();
        }
    };
    
    // Запуск при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

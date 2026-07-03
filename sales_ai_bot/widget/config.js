// Конфигурация виджета
window.SalesAIConfig = {
    // URL вашего API
    apiUrl: 'http://localhost:8000',
    
    // Тип клиента по умолчанию
    defaultClientType: 'msb',
    
    // Настройки внешнего вида
    theme: {
        primaryColor: '#667eea',
        secondaryColor: '#764ba2',
        textColor: '#333',
        backgroundColor: '#fff',
        userMessageBg: '#667eea',
        botMessageBg: '#f0f0f0',
    },
    
    // Тексты
    texts: {
        welcomeMessage: 'Здравствуйте! Я AI-ассистент отдела продаж. Чем могу помочь?',
        placeholder: 'Напишите ваш вопрос...',
        sendButton: 'Отправить',
        error: 'Извините, произошла ошибка. Попробуйте позже.',
    },
    
    // Поведение
    behavior: {
        autoOpen: false,  // Автоматически открывать чат
        soundEnabled: true,  // Звук новых сообщений
    }
};

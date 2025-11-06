let currentLanguage = 'en';

function showMessage(text, type = 'success') {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message show ${type}`;
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 5000);
}

function updateStatus(running) {
    const statusEl = document.getElementById('status');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (running) {
        statusEl.textContent = '🟢 Bot is running...';
        statusEl.className = 'status active running';
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        statusEl.textContent = '🔴 Bot is stopped';
        statusEl.className = 'status active stopped';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

async function startBot() {
    const token = document.getElementById('token').value.trim();
    const channelId = document.getElementById('channel_id').value.trim();
    const language = document.getElementById('language').value;
    
    if (!token || !channelId) {
        showMessage('Please enter both Token and Channel ID', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: token,
                channel_id: channelId,
                language: language
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Bot started successfully!', 'success');
            updateStatus(true);
            currentLanguage = language;
        } else {
            showMessage(data.message || 'Failed to start bot', 'error');
        }
    } catch (error) {
        showMessage('Error starting bot: ' + error.message, 'error');
    }
}

async function stopBot() {
    try {
        const response = await fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Bot stopped successfully!', 'success');
            updateStatus(false);
        } else {
            showMessage(data.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        showMessage('Error stopping bot: ' + error.message, 'error');
    }
}

async function changeLanguage() {
    const language = document.getElementById('language').value;
    
    if (currentLanguage === language) {
        return;
    }
    
    try {
        const response = await fetch('/api/change-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                language: language
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentLanguage = language;
            showMessage(`Language changed to ${language === 'en' ? 'English' : 'Português'}`, 'success');
        }
    } catch (error) {
        showMessage('Error changing language: ' + error.message, 'error');
    }
}

// Check bot status on page load
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateStatus(data.running);
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Event listeners
document.getElementById('language').addEventListener('change', changeLanguage);

// Check status periodically
setInterval(checkStatus, 3000);

// Initial status check
checkStatus();


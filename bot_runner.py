#!/usr/bin/env python3
"""
🤖 Bac-Bo Bot Web Controller
=========================
Web-based bot controller with modern UI accessible via URL.
Users can control the bot through a web interface.
"""

import os
import sys
import asyncio
import random
import time
import threading
from datetime import datetime
from typing import Optional
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("Error: python-telegram-bot is not installed.")
    print("Please install it using: pip install python-telegram-bot")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Translations
TRANSLATIONS = {
    'en': {
        'title': '🤖 Bac-Bo Bot Controller',
        'bot_token': 'Telegram Bot Token:',
        'channel_id': 'Telegram Channel ID:',
        'language': 'Language:',
        'start_bot': 'Start Bot',
        'stop_bot': 'Stop Bot',
        'status': 'Status:',
        'status_stopped': 'Stopped',
        'status_running': 'Bot Running...',
        'activity_log': 'Activity Log:',
        'messages': {
            'bot_started': '✅ Bot started',
            'bot_stopped': '⛔ Bot stopped',
            'opening_site': '🌐 Opening the site...',
            'looking_login_button': '🔍 Looking for the login button...',
            'looking_email_field': '🔍 Looking for the email field...',
            'filling_email': '✏️ Filling email field...',
            'looking_password_field': '🔍 Looking for the password field...',
            'filling_password': '✏️ Filling password field...',
            'clicking_login': '🖱️ Clicking login button...',
            'monitoring_game': '👁️ Monitoring the game...',
            'probabilities': 'PROBABILITIES',
            'player': 'Player',
            'banker': 'Banker',
            'tie': 'Tie',
            'game_result': 'GAME RESULT',
            'winner_player': 'WINNER: PLAYER',
            'winner_banker': 'WINNER: BANKER',
            'player_wins_round': 'Player wins this round!',
            'banker_wins_round': 'Banker wins this round!',
            'its_draw': "It's a draw!",
            'win_loss_record': 'WIN/LOSS RECORD',
            'total_wins': 'Total Wins',
            'total_losses': 'Total Losses',
            'win_rate': 'Win Rate',
            'statistics': 'STATISTICS',
            'bettors': 'bettors',
        },
        'errors': {
            'token_required': 'Please enter a Telegram Bot Token',
            'channel_required': 'Please enter a Telegram Channel ID',
            'invalid_token': 'Invalid bot token format',
        }
    },
    'pt': {
        'title': '🤖Controlador do Bot Bac-Bo',
        'bot_token': 'Token do Bot Telegram:',
        'channel_id': 'ID do Canal Telegram:',
        'language': 'Idioma:',
        'start_bot': 'Iniciar Bot',
        'stop_bot': 'Parar Bot',
        'status': 'Status:',
        'status_stopped': 'Parado',
        'status_running': 'Bot em Execução...',
        'activity_log': 'Registro de Atividades:',
        'messages': {
            'bot_started': '✅ Bot iniciado',
            'bot_stopped': '⛔ Bot parado',
            'opening_site': '🌐 Abrindo o site...',
            'looking_login_button': '🔍 Procurando o botão de login...',
            'looking_email_field': '🔍 Procurando o campo de email...',
            'filling_email': '✏️ Preenchendo campo de email...',
            'looking_password_field': '🔍 Procurando o campo de senha...',
            'filling_password': '✏️ Preenchendo campo de senha...',
            'clicking_login': '🖱️ Clicando no botão de login...',
            'monitoring_game': '👁️ Monitorando o jogo...',
            'probabilities': 'PROBABILIDADES',
            'player': 'Jogador',
            'banker': 'Banco',
            'tie': 'Empate',
            'game_result': 'RESULTADO DO JOGO',
            'winner_player': 'VENCEDOR: JOGADOR',
            'winner_banker': 'VENCEDOR: BANCO',
            'player_wins_round': 'Jogador vence esta rodada!',
            'banker_wins_round': 'Banco vence esta rodada!',
            'its_draw': 'É um empate!',
            'win_loss_record': 'REGISTRO DE VITÓRIAS/DERROTAS',
            'total_wins': 'Total de Vitórias',
            'total_losses': 'Total de Derrotas',
            'win_rate': 'Taxa de Vitória',
            'statistics': 'ESTATÍSTICAS',
            'bettors': 'apostadores',
        },
        'errors': {
            'token_required': 'Por favor, insira um Token do Bot Telegram',
            'channel_required': 'Por favor, insira um ID do Canal Telegram',
            'invalid_token': 'Formato de token inválido',
        }
    }
}

# Global bot instance
bot_instance = None
bot_lock = threading.Lock()

class HeadlessBot:
    """Headless version of the bot for Railway deployment."""
    
    def __init__(self, bot_token: str, channel_id: str, language: str = 'en'):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.language = language.lower()
        self.email = 'firdausjulkifli0729@gmail.com'
        self.password = 'kok060729'
        
        self.translations = TRANSLATIONS.get(self.language, TRANSLATIONS['en'])
        self.bot: Optional[Bot] = None
        self.is_running = False
        self.message_task: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.message_loop_loop = None  # Store the event loop for sending stop message
        
        # Win/Loss counters
        self.total_wins = 0
        self.total_losses = 0
        
        # Activity log
        self.activity_log = []
        self.max_log_entries = 100
        
    def log_activity(self, message: str):
        """Add message to activity log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f'[{timestamp}] {message}'
        self.activity_log.append(log_entry)
        if len(self.activity_log) > self.max_log_entries:
            self.activity_log.pop(0)
        print(log_entry)
    
    async def send_telegram_message(self, message: str) -> bool:
        """Send a message to Telegram channel."""
        try:
            if self.bot:
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return True
        except TelegramError as e:
            self.log_activity(f'Telegram Error: {str(e)}')
            return False
        except Exception as e:
            self.log_activity(f'Error: {str(e)}')
            return False
        return False
    
    def generate_random_result(self) -> tuple[str, str]:
        """Generate a random game result message."""
        # Generate random odds - tie must be at least 10%
        tie_odds = random.randint(10, 20)
        remaining = 100 - tie_odds
        
        player_odds = remaining // 2 + random.randint(-5, 5)
        banker_odds = remaining - player_odds
        
        if player_odds < 35:
            player_odds = 35
            banker_odds = remaining - player_odds
        elif banker_odds < 35:
            banker_odds = 35
            player_odds = remaining - banker_odds
        
        # Format odds message
        odds_msg = f"📊 **{self.translations['messages']['probabilities']}** 📊\n"
        odds_msg += f"🟢 {self.translations['messages']['player']}: **{player_odds}%**\n"
        odds_msg += f"🔴 {self.translations['messages']['banker']}: **{banker_odds}%**\n"
        odds_msg += f"🔵 {self.translations['messages']['tie']}: **{tie_odds}%**"
        
        # Generate random outcome
        outcomes = ['player', 'banker', 'tie']
        weights = [player_odds, banker_odds, tie_odds]
        outcome_type = random.choices(outcomes, weights=weights)[0]
        
        # Update counters
        if outcome_type == 'tie':
            self.total_losses += 1
        else:
            self.total_wins += 1
        
        # Format result message
        result_msg = f"🎯 **{self.translations['messages']['game_result']}** 🎯\n\n"
        
        if outcome_type == 'player':
            result_msg += f"✅ **{self.translations['messages']['winner_player']}** 🟢\n"
            result_msg += f"🎉 {self.translations['messages']['player_wins_round']}\n\n"
        elif outcome_type == 'banker':
            result_msg += f"✅ **{self.translations['messages']['winner_banker']}** 🔴\n"
            result_msg += f"🎉 {self.translations['messages']['banker_wins_round']}\n\n"
        else:
            result_msg += f"⚖️ **{self.translations['messages']['tie']}** 🔵\n"
            result_msg += f"🤝 {self.translations['messages']['its_draw']}\n\n"
        
        # Win/Loss record
        result_msg += f"📊 **{self.translations['messages']['win_loss_record']}** 📊\n"
        result_msg += f"✅ {self.translations['messages']['total_wins']}: **{self.total_wins}**\n"
        result_msg += f"❌ {self.translations['messages']['total_losses']}: **{self.total_losses}**\n"
        total_games = self.total_wins + self.total_losses
        if total_games > 0:
            win_rate = (self.total_wins / total_games) * 100
            result_msg += f"📈 {self.translations['messages']['win_rate']}: **{win_rate:.1f}%**\n"
        result_msg += "\n"
        
        # Statistics
        players_betting = random.randint(150, 850)
        bankers_betting = random.randint(120, 780)
        
        remaining_percentage = 100 - tie_odds
        total_bets = players_betting + bankers_betting
        if total_bets > 0:
            player_ratio = players_betting / total_bets
            banker_ratio = bankers_betting / total_bets
            
            player_percentage = remaining_percentage * player_ratio
            banker_percentage = remaining_percentage * banker_ratio
            
            result_msg += f"📈 **{self.translations['messages']['statistics']}** 📈\n"
            result_msg += f"🟢 {self.translations['messages']['player']}: **{player_percentage:.1f}%** ({players_betting} {self.translations['messages']['bettors']})\n"
            result_msg += f"🔴 {self.translations['messages']['banker']}: **{banker_percentage:.1f}%** ({bankers_betting} {self.translations['messages']['bettors']})\n"
            result_msg += f"🔵 {self.translations['messages']['tie']}: **{tie_odds}%**"
        
        return odds_msg, result_msg
    
    async def async_message_loop(self):
        """Async message loop."""
        try:
            self.log_activity('Message loop started')
            
            # Step 1: Bot started
            await self.send_telegram_message(self.translations['messages']['bot_started'])
            self.log_activity('Bot started message sent')
            
            # Step 2: Opening the site
            await asyncio.sleep(1)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['opening_site'])
            self.log_activity('Opening site message sent')
            
            # Step 3: Wait 5 seconds, then looking for login button
            await asyncio.sleep(5)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['looking_login_button'])
            self.log_activity('Looking for login button message sent')
            
            # Step 4: Wait 5 seconds, then looking for email field
            await asyncio.sleep(5)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['looking_email_field'])
            self.log_activity('Looking for email field message sent')
            
            # Step 5: Wait 2 seconds, then filling email
            await asyncio.sleep(2)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['filling_email'])
            self.log_activity(f'Filling email message sent - Email: {self.email}')
            
            # Step 6: Wait 5 seconds, then looking for password field
            await asyncio.sleep(5)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['looking_password_field'])
            self.log_activity('Looking for password field message sent')
            
            # Step 7: Wait 2 seconds, then filling password
            await asyncio.sleep(2)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['filling_password'])
            self.log_activity(f'Filling password message sent - Password: {self.password}')
            
            # Step 8: Wait 5 seconds, then clicking login button
            await asyncio.sleep(5)
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['clicking_login'])
            self.log_activity('Clicking login button message sent')
            
            # Step 9: Monitoring the game
            if not self.is_running:
                return
            await self.send_telegram_message(self.translations['messages']['monitoring_game'])
            self.log_activity('Monitoring game message sent')
            
            # Step 10: Main loop - send random results every 12 seconds
            while self.is_running:
                try:
                    await asyncio.sleep(12)
                    
                    if not self.is_running:
                        break
                    
                    # Generate and send random odds and result
                    odds_msg, result_msg = self.generate_random_result()
                    
                    # Send odds message
                    await self.send_telegram_message(odds_msg)
                    self.log_activity('Sent odds message')
                    
                    # Small delay between odds and result
                    await asyncio.sleep(1)
                    
                    if not self.is_running:
                        break
                    
                    # Send result message
                    await self.send_telegram_message(result_msg)
                    self.log_activity('Sent result message')
                    
                except Exception as e:
                    self.log_activity(f'Error in message loop: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(1)
            
            self.log_activity('Message loop ended')
            
        except Exception as e:
            self.log_activity(f'Fatal error in message_loop: {str(e)}')
            import traceback
            traceback.print_exc()
        finally:
            # Send stop message if bot exists (regardless of is_running status)
            if self.bot:
                try:
                    await self.send_telegram_message(self.translations['messages']['bot_stopped'])
                    self.log_activity('Bot stopped message sent')
                except Exception as e:
                    self.log_activity(f'Failed to send stop message: {str(e)}')
            self.is_running = False
    
    def message_loop(self):
        """Main message loop running in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.message_loop_loop = loop  # Store reference for stop() method
        try:
            loop.run_until_complete(self.async_message_loop())
        finally:
            self.message_loop_loop = None
            loop.close()
    
    def start(self):
        """Start the bot."""
        try:
            self.bot = Bot(token=self.bot_token)
            self.is_running = True
            self.stop_event.clear()
            self.total_wins = 0
            self.total_losses = 0
            
            self.message_task = threading.Thread(target=self.message_loop, daemon=True)
            self.message_task.start()
            self.log_activity('Bot initialization started')
            return True
        except Exception as e:
            self.log_activity(f'Failed to start bot: {str(e)}')
            self.is_running = False
            return False
    
    def change_language(self, new_language: str):
        """Change the bot's language dynamically."""
        new_lang = new_language.lower()
        if new_lang in TRANSLATIONS:
            old_language = self.language
            self.language = new_lang
            self.translations = TRANSLATIONS[new_lang]
            self.log_activity(f'Language changed from {old_language} to {new_lang}')
            return True
        return False
    
    def stop(self):
        """Stop the bot."""
        was_running = self.is_running
        self.is_running = False
        self.stop_event.set()
        self.log_activity('Bot stop requested')
        
        # If bot was running and we have a bot instance, try to send stop message immediately
        # This ensures the message is sent even if the message loop hasn't reached the finally block yet
        if was_running and self.bot and self.message_loop_loop:
            try:
                # Use the message loop's event loop to send the stop message
                future = asyncio.run_coroutine_threadsafe(
                    self.send_telegram_message(self.translations['messages']['bot_stopped']),
                    self.message_loop_loop
                )
                # Wait up to 2 seconds for the message to be sent
                future.result(timeout=2.0)
                self.log_activity('Bot stopped message sent (from stop method)')
            except Exception as e:
                self.log_activity(f'Could not send stop message immediately: {str(e)}')
                # The finally block in async_message_loop will try to send it
        
        # Wait for message thread to finish (with timeout)
        if self.message_task and self.message_task.is_alive():
            self.message_task.join(timeout=5.0)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Bac-Bo Bot Controller</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .button-group {
            display: flex;
            gap: 15px;
            margin: 30px 0;
        }
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-start {
            background: #4CAF50;
            color: white;
        }
        .btn-start:hover:not(:disabled) {
            background: #45a049;
        }
        .btn-stop {
            background: #f44336;
            color: white;
        }
        .btn-stop:hover:not(:disabled) {
            background: #da190b;
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        .status-stopped {
            background: #f5f5f5;
            color: #666;
        }
        .status-running {
            background: #e8f5e9;
            color: #4CAF50;
        }
        .log-container {
            margin-top: 20px;
        }
        .log-label {
            font-weight: bold;
            margin-bottom: 10px;
            color: #555;
        }
        .log-box {
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.6;
        }
        .log-entry {
            margin-bottom: 5px;
            color: #333;
        }
        .error {
            color: #f44336;
        }
        .success {
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 id="title">🤖 Bac-Bo Bot Controller</h1>
        
        <div class="form-group">
            <label id="label-token">Telegram Bot Token:</label>
            <input type="text" id="bot-token" placeholder="Enter your Telegram Bot Token">
        </div>
        
        <div class="form-group">
            <label id="label-channel">Telegram Channel ID:</label>
            <input type="text" id="channel-id" placeholder="Enter your Telegram Channel ID">
        </div>
        
        <div class="form-group">
            <label id="label-language">Language:</label>
            <select id="language">
                <option value="en">English 🇬🇧</option>
                <option value="pt">Portuguese 🇵🇹</option>
            </select>
        </div>
        
        <div class="button-group">
            <button class="btn-start" id="btn-start" onclick="startBot()">Start Bot</button>
            <button class="btn-stop" id="btn-stop" onclick="stopBot()" disabled>Stop Bot</button>
        </div>
        
        <div class="status status-stopped" id="status">
            <span id="status-text">Status: Stopped</span>
        </div>
        
        <div class="log-container">
            <div class="log-label" id="log-label">Activity Log:</div>
            <div class="log-box" id="log-box"></div>
        </div>
    </div>
    
    <script>
        let currentLanguage = 'en';
        const translations = {
            en: {
                title: '🤖 Bac-Bo Bot Controller',
                bot_token: 'Telegram Bot Token:',
                channel_id: 'Telegram Channel ID:',
                language: 'Language:',
                start_bot: 'Start Bot',
                stop_bot: 'Stop Bot',
                status: 'Status:',
                status_stopped: 'Stopped',
                status_running: 'Bot Running...',
                activity_log: 'Activity Log:'
            },
            pt: {
                title: '🤖 Controlador do Bot Bac-Bo',
                bot_token: 'Token do Bot Telegram:',
                channel_id: 'ID do Canal Telegram:',
                language: 'Idioma:',
                start_bot: 'Iniciar Bot',
                stop_bot: 'Parar Bot',
                status: 'Status:',
                status_stopped: 'Parado',
                status_running: 'Bot em Execução...',
                activity_log: 'Registro de Atividades:'
            }
        };
        
        function updateUI() {
            const t = translations[currentLanguage];
            document.getElementById('title').textContent = t.title;
            document.getElementById('label-token').textContent = t.bot_token;
            document.getElementById('label-channel').textContent = t.channel_id;
            document.getElementById('label-language').textContent = t.language;
            document.getElementById('btn-start').textContent = t.start_bot;
            document.getElementById('btn-stop').textContent = t.stop_bot;
            document.getElementById('log-label').textContent = t.activity_log;
            updateStatus();
        }
        
        function updateStatus() {
            const t = translations[currentLanguage];
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    const statusText = document.getElementById('status-text');
                    if (data.running) {
                        statusEl.className = 'status status-running';
                        statusText.textContent = t.status + ' ' + t.status_running;
                        document.getElementById('btn-start').disabled = true;
                        document.getElementById('btn-stop').disabled = false;
                    } else {
                        statusEl.className = 'status status-stopped';
                        statusText.textContent = t.status + ' ' + t.status_stopped;
                        document.getElementById('btn-start').disabled = false;
                        document.getElementById('btn-stop').disabled = true;
                    }
                });
        }
        
        function addLog(message, type = '') {
            const logBox = document.getElementById('log-box');
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + type;
            entry.textContent = message;
            logBox.appendChild(entry);
            logBox.scrollTop = logBox.scrollHeight;
        }
        
        function startBot() {
            const token = document.getElementById('bot-token').value.trim();
            const channelId = document.getElementById('channel-id').value.trim();
            const language = document.getElementById('language').value;
            
            if (!token) {
                alert(translations[currentLanguage].bot_token.replace(':', '') + ' is required!');
                return;
            }
            if (!channelId) {
                alert(translations[currentLanguage].channel_id.replace(':', '') + ' is required!');
                return;
            }
            
            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token, channel_id: channelId, language})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    addLog('Bot started successfully', 'success');
                    updateStatus();
                } else {
                    addLog('Error: ' + data.error, 'error');
                }
            })
            .catch(err => {
                addLog('Error: ' + err.message, 'error');
            });
        }
        
        function stopBot() {
            fetch('/api/stop', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    addLog('Bot stopped', 'success');
                    updateStatus();
                }
            });
        }
        
        function loadLogs() {
            fetch('/api/logs')
                .then(r => r.json())
                .then(data => {
                    const logBox = document.getElementById('log-box');
                    logBox.innerHTML = '';
                    data.logs.forEach(log => {
                        addLog(log);
                    });
                });
        }
        
        document.getElementById('language').addEventListener('change', (e) => {
            const newLanguage = e.target.value;
            currentLanguage = newLanguage;
            updateUI();
            
            // If bot is running, change its language dynamically
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    if (data.running) {
                        fetch('/api/change-language', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({language: newLanguage})
                        })
                        .then(r => r.json())
                        .then(result => {
                            if (result.success) {
                                addLog(`Language changed to ${newLanguage === 'en' ? 'English' : 'Portuguese'}`, 'success');
                            } else {
                                addLog('Failed to change language: ' + result.error, 'error');
                            }
                        })
                        .catch(err => {
                            addLog('Error changing language: ' + err.message, 'error');
                        });
                    }
                });
        });
        
        // Update status and logs every 2 seconds
        setInterval(() => {
            updateStatus();
            loadLogs();
        }, 2000);
        
        // Initial load
        updateUI();
        loadLogs();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start the bot."""
    global bot_instance
    
    try:
        with bot_lock:
            if bot_instance and bot_instance.is_running:
                return jsonify({'success': False, 'error': 'Bot is already running'})
            
            if not request.json:
                return jsonify({'success': False, 'error': 'Invalid request data'})
            
            data = request.json
            bot_token = data.get('token', '').strip()
            channel_id = data.get('channel_id', '').strip()
            language = data.get('language', 'en').lower()
            
            if not bot_token:
                return jsonify({'success': False, 'error': 'Bot token is required'})
            if not channel_id:
                return jsonify({'success': False, 'error': 'Channel ID is required'})
            if len(bot_token) < 20:
                return jsonify({'success': False, 'error': 'Invalid bot token format'})
            
            bot_instance = HeadlessBot(bot_token, channel_id, language)
            if bot_instance.start():
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to start bot'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the bot."""
    global bot_instance
    
    try:
        with bot_lock:
            if bot_instance:
                bot_instance.stop()
                bot_instance = None
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Get bot status."""
    global bot_instance
    
    with bot_lock:
        if bot_instance:
            return jsonify({
                'running': bot_instance.is_running,
                'language': bot_instance.language
            })
        return jsonify({'running': False, 'language': 'en'})

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """Get activity logs."""
    global bot_instance
    
    with bot_lock:
        if bot_instance:
            return jsonify({'logs': bot_instance.activity_log})
        return jsonify({'logs': []})

@app.route('/api/change-language', methods=['POST'])
def api_change_language():
    """Change the bot's language dynamically."""
    global bot_instance
    
    try:
        if not request.json:
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        data = request.json
        new_language = data.get('language', 'en').lower()
        
        if new_language not in TRANSLATIONS:
            return jsonify({'success': False, 'error': f'Invalid language: {new_language}'})
        
        with bot_lock:
            if bot_instance:
                if bot_instance.change_language(new_language):
                    return jsonify({'success': True, 'language': new_language})
                else:
                    return jsonify({'success': False, 'error': 'Failed to change language'})
            else:
                return jsonify({'success': False, 'error': 'Bot is not running'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway."""
    return jsonify({'status': 'ok', 'service': 'bac-bo-bot'}), 200

if __name__ == '__main__':
    # Railway sets PORT environment variable
    port = int(os.getenv('PORT', 5000))
    # Run on all interfaces (0.0.0.0) to accept external connections
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

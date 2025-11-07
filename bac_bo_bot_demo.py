#!/usr/bin/env python3
"""
Bac-Bo Bot Controller - Demo Version
=====================================
A production-style Python demo that simulates a Telegram automation bot
with a modern graphical UI. This version sends random fake results at
random intervals (15-30 seconds) to demonstrate the bot flow.

Requirements:
    - Python 3.8+
    - python-telegram-bot >= 20.0
    - tkinter (usually included with Python)

Installation:
    pip install python-telegram-bot

Usage:
    python bac_bo_bot_demo.py
"""

import asyncio
import random
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Optional
import sys

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("Error: python-telegram-bot is not installed.")
    print("Please install it using: pip install python-telegram-bot")
    sys.exit(1)


# ============================================================================
# Language Translations
# ============================================================================

TRANSLATIONS = {
    'en': {
        'title': 'Bac-Bo Bot Controller',
        'bot_token': 'Telegram Bot Token:',
        'channel_id': 'Telegram Channel ID:',
        'language': 'Language:',
        'start_bot': 'Start Bot',
        'stop_bot': 'Stop Bot',
        'status': 'Status:',
        'status_stopped': 'Stopped',
        'status_running': 'Bot Running...',
        'status_starting': 'Starting...',
        'status_stopping': 'Stopping...',
        'activity_log': 'Activity Log:',
        'email': 'Email:',
        'password': 'Password:',
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
            'player_wins': '🟢 Player wins',
            'banker_wins': '🔴 Banker wins',
            'draw': '🔵 Draw',
            'odds_format': 'Player: {player}% | Banker: {banker}% | Tie: {tie}%',
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
            'email_required': 'Please enter an email address',
            'password_required': 'Please enter a password',
            'invalid_token': 'Invalid bot token format',
            'connection_error': 'Failed to connect to Telegram. Please check your token and internet connection.',
        }
    },
    'pt': {
        'title': 'Controlador do Bot Bac-Bo',
        'bot_token': 'Token do Bot Telegram:',
        'channel_id': 'ID do Canal Telegram:',
        'language': 'Idioma:',
        'start_bot': 'Iniciar Bot',
        'stop_bot': 'Parar Bot',
        'status': 'Status:',
        'status_stopped': 'Parado',
        'status_running': 'Bot em Execução...',
        'status_starting': 'Iniciando...',
        'status_stopping': 'Parando...',
        'activity_log': 'Registro de Atividades:',
        'email': 'Email:',
        'password': 'Senha:',
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
            'player_wins': '🟢 Jogador vence',
            'banker_wins': '🔴 Banco vence',
            'draw': '🔵 Empate',
            'odds_format': 'Jogador: {player}% | Banco: {banker}% | Empate: {tie}%',
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
            'email_required': 'Por favor, insira um endereço de email',
            'password_required': 'Por favor, insira uma senha',
            'invalid_token': 'Formato de token inválido',
            'connection_error': 'Falha ao conectar ao Telegram. Verifique seu token e conexão com a internet.',
        }
    }
}


# ============================================================================
# Bot Controller Class
# ============================================================================

class BacBoBotController:
    """Main controller class for the Bac-Bo Bot demo."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_language = 'en'
        self.translations = TRANSLATIONS[self.current_language]
        
        # Bot state
        self.bot: Optional[Bot] = None
        self.bot_token: str = ''
        self.channel_id: str = ''
        # Hardcoded credentials
        self.email: str = 'firdausjulkifli0729@gmail.com'
        self.password: str = 'kok060729'
        self.is_running = False
        self.message_task: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Store event loop reference for stop message
        self.message_loop_event_loop = None
        
        # Win/Loss counters
        self.total_wins = 0
        self.total_losses = 0
        
        # Setup UI
        self.setup_ui()
        
        # Center window
        self.center_window()
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = 600
        height = 500
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the modern UI components."""
        # Configure root window
        self.root.title(self.translations['title'])
        self.root.resizable(False, False)
        self.root.configure(bg='#f5f5f5')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for modern flat theme
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('Start.TButton', background='#4CAF50', foreground='white')
        style.configure('Stop.TButton', background='#f44336', foreground='white')
        style.map('Start.TButton', background=[('active', '#45a049')])
        style.map('Stop.TButton', background=[('active', '#da190b')])
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(
            main_frame,
            text=self.translations['title'],
            font=('Segoe UI', 18, 'bold'),
            bg='#f5f5f5',
            fg='#333333'
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Bot Token field
        self.token_label = ttk.Label(main_frame, text=self.translations['bot_token'])
        self.token_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.token_entry = ttk.Entry(main_frame, width=50, font=('Consolas', 9))
        self.token_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Channel ID field
        self.channel_label = ttk.Label(main_frame, text=self.translations['channel_id'])
        self.channel_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.channel_entry = ttk.Entry(main_frame, width=50, font=('Consolas', 9))
        self.channel_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Language selector
        self.lang_label = ttk.Label(main_frame, text=self.translations['language'])
        self.lang_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.language_var = tk.StringVar(value='English 🇬🇧')
        language_combo = ttk.Combobox(
            main_frame,
            textvariable=self.language_var,
            values=['English 🇬🇧', 'Portuguese 🇵🇹'],
            state='readonly',
            width=47
        )
        language_combo.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(
            button_frame,
            text=self.translations['start_bot'],
            style='Start.TButton',
            command=self.start_bot,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text=self.translations['stop_bot'],
            style='Stop.TButton',
            command=self.stop_bot,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text=self.translations['status'])
        self.status_label.pack(side=tk.LEFT)
        
        self.status_value = tk.Label(
            status_frame,
            text=self.translations['status_stopped'],
            font=('Segoe UI', 10, 'bold'),
            bg='#f5f5f5',
            fg='#666666'
        )
        self.status_value.pack(side=tk.LEFT, padx=(10, 0))
        
        # Activity log (optional, for better UX)
        self.log_label = ttk.Label(main_frame, text=self.translations['activity_log'], font=('Segoe UI', 10, 'bold'))
        self.log_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=8,
            width=70,
            font=('Consolas', 8),
            bg='#ffffff',
            fg='#333333',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.log_text.grid(row=7, column=0, columnspan=2, pady=5)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str):
        """Add a message to the activity log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f'[{timestamp}] {message}\n'
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def on_language_change(self, event=None):
        """Handle language change event."""
        selected = self.language_var.get()
        if 'English' in selected:
            self.current_language = 'en'
        else:
            self.current_language = 'pt'
        
        self.translations = TRANSLATIONS[self.current_language]
        self.update_ui_text()
    
    def update_ui_text(self):
        """Update all UI text elements with current language."""
        self.root.title(self.translations['title'])
        self.token_label.config(text=self.translations['bot_token'])
        self.channel_label.config(text=self.translations['channel_id'])
        self.lang_label.config(text=self.translations['language'])
        self.status_label.config(text=self.translations['status'])
        self.start_button.config(text=self.translations['start_bot'])
        self.stop_button.config(text=self.translations['stop_bot'])
        self.log_label.config(text=self.translations['activity_log'])
        
        # Update status value if bot is stopped
        if not self.is_running:
            self.status_value.config(text=self.translations['status_stopped'])
    
    def validate_inputs(self) -> bool:
        """Validate user inputs."""
        self.bot_token = self.token_entry.get().strip()
        self.channel_id = self.channel_entry.get().strip()
        # Email and password are hardcoded, no need to get from UI
        
        if not self.bot_token:
            messagebox.showerror(
                'Error',
                self.translations['errors']['token_required']
            )
            return False
        
        if not self.channel_id:
            messagebox.showerror(
                'Error',
                self.translations['errors']['channel_required']
            )
            return False
        
        # Basic token format validation (Telegram bot tokens are typically long)
        if len(self.bot_token) < 20:
            messagebox.showerror(
                'Error',
                self.translations['errors']['invalid_token']
            )
            return False
        
        return True
    
    async def send_telegram_message(self, message: str) -> bool:
        """Send a message to Telegram channel."""
        try:
            if not self.bot:
                error_msg = 'Bot instance not available'
                self.log_message(error_msg)
                print(f"Error: {error_msg}")
                return False
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except TelegramError as e:
            error_msg = f'Telegram Error: {str(e)}'
            self.log_message(error_msg)
            print(f"Telegram Error: {e}")
            return False
        except Exception as e:
            error_msg = f'Error sending message: {str(e)}'
            self.log_message(error_msg)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_async_send(self, message: str, loop: asyncio.AbstractEventLoop):
        """Run async send_telegram_message using the provided event loop."""
        try:
            # Since we're in the same thread as the event loop, use run_until_complete
            loop.run_until_complete(self.send_telegram_message(message))
        except Exception as e:
            error_msg = f'Async Error sending "{message[:50]}...": {str(e)}'
            self.log_message(error_msg)
            print(f"Error sending message: {e}")  # Also print to console for debugging
            import traceback
            traceback.print_exc()
    
    def generate_random_result(self) -> tuple[str, str]:
        """Generate a random game result message with modern professional formatting.
        Returns: (odds_message, result_message)
        """
        # Generate random odds - tie must be at least 10%
        tie_odds = random.randint(10, 20)  # 10-20% chance for tie
        remaining = 100 - tie_odds
        
        # Player and Banker split the remaining odds (roughly equal, slight variation)
        player_odds = remaining // 2 + random.randint(-5, 5)
        banker_odds = remaining - player_odds
        
        # Ensure both are reasonable (at least 35%)
        if player_odds < 35:
            player_odds = 35
            banker_odds = remaining - player_odds
        elif banker_odds < 35:
            banker_odds = 35
            player_odds = remaining - banker_odds
        
        # Format modern odds message
        odds_msg = f"📊 **{self.translations['messages']['probabilities']}** 📊\n"
        odds_msg += f"🟢 {self.translations['messages']['player']}: **{player_odds}%**\n"
        odds_msg += f"🔴 {self.translations['messages']['banker']}: **{banker_odds}%**\n"
        odds_msg += f"🔵 {self.translations['messages']['tie']}: **{tie_odds}%**"
        
        # Generate random outcome based on odds
        outcomes = ['player', 'banker', 'tie']
        weights = [player_odds, banker_odds, tie_odds]
        outcome_type = random.choices(outcomes, weights=weights)[0]
        
        # Update win/loss counters
        # Player and Banker wins count as wins, Tie counts as loss
        if outcome_type == 'tie':
            self.total_losses += 1
        else:
            self.total_wins += 1
        
        # Format modern professional result message
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
        
        # Add Win/Loss statistics (sequential results from bot start)
        result_msg += f"📊 **{self.translations['messages']['win_loss_record']}** 📊\n"
        result_msg += f"✅ {self.translations['messages']['total_wins']}: **{self.total_wins}**\n"
        result_msg += f"❌ {self.translations['messages']['total_losses']}: **{self.total_losses}**\n"
        total_games = self.total_wins + self.total_losses
        if total_games > 0:
            win_rate = (self.total_wins / total_games) * 100
            result_msg += f"📈 {self.translations['messages']['win_rate']}: **{win_rate:.1f}%**\n"
        result_msg += "\n"
        
        # Add statistics section - Random current active players (simulating real site data)
        # Generate random numbers of users currently playing/betting (NO TIE - only Player and Banker)
        players_betting = random.randint(150, 850)  # Random number of users betting on Player
        bankers_betting = random.randint(120, 780)  # Random number of users betting on Banker
        
        # Calculate percentages - must total 100% including Tie
        # Tie percentage is fixed from probabilities, Player and Banker split the remaining
        remaining_percentage = 100 - tie_odds  # Remaining percentage for Player and Banker
        
        # Calculate relative distribution between Player and Banker based on bettors
        total_bets = players_betting + bankers_betting
        if total_bets > 0:
            # Get the ratio of Player to Banker bettors
            player_ratio = players_betting / total_bets
            banker_ratio = bankers_betting / total_bets
            
            # Apply these ratios to the remaining percentage (after Tie)
            player_percentage = remaining_percentage * player_ratio
            banker_percentage = remaining_percentage * banker_ratio
            
            result_msg += f"📈 **{self.translations['messages']['statistics']}** 📈\n"
            result_msg += f"🟢 {self.translations['messages']['player']}: **{player_percentage:.1f}%** ({players_betting} {self.translations['messages']['bettors']})\n"
            result_msg += f"🔴 {self.translations['messages']['banker']}: **{banker_percentage:.1f}%** ({bankers_betting} {self.translations['messages']['bettors']})\n"
            result_msg += f"🔵 {self.translations['messages']['tie']}: **{tie_odds}%**"
        
        return odds_msg, result_msg
    
    def safe_wait(self, seconds: float) -> bool:
        """Wait for specified seconds, return True if stopped."""
        if self.stop_event.wait(seconds):
            return True
        return False
    
    def send_message_safe(self, message: str, log_msg: str = None, loop: asyncio.AbstractEventLoop = None):
        """Send a message safely, logging any errors but continuing."""
        try:
            print(f"Sending message: {message[:50]}...")  # Debug output
            if loop:
                self.run_async_send(message, loop)
            else:
                # Fallback: create a new event loop if none provided
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(self.send_telegram_message(message))
                finally:
                    new_loop.close()
            # Small delay to ensure message is sent before continuing
            time.sleep(0.5)
            if log_msg:
                self.log_message(log_msg)
            print(f"Message sent successfully: {message[:50]}...")  # Debug output
        except Exception as e:
            error_msg = f'Error sending message: {str(e)}'
            self.log_message(error_msg)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def message_loop(self):
        """Main message loop that sends detailed step-by-step messages."""
        # Create a single event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Store loop reference for stop message
        self.message_loop_event_loop = loop
        
        try:
            self.log_message('Message loop thread started')
            print("Message loop thread started")
            
            # Step 1: Bot started
            self.send_message_safe(
                self.translations['messages']['bot_started'],
                'Bot started message sent',
                loop
            )
            
            # Step 2: Opening the site (immediately after start)
            if not self.safe_wait(1):
                self.send_message_safe(
                    self.translations['messages']['opening_site'],
                    'Opening the site... https://www.vemabet10.com/pt/game/bac-bo/play-for-real',
                    loop
                )
            
            # Step 3: Wait 5 seconds, then looking for login button
            if not self.safe_wait(5):
                self.send_message_safe(
                    self.translations['messages']['looking_login_button'],
                    'Looking for login button...',
                    loop
                )
            
            # Step 4: Wait 5 seconds, then looking for email field
            if not self.safe_wait(5):
                self.send_message_safe(
                    self.translations['messages']['looking_email_field'],
                    'Looking for email field...',
                    loop
                )
            
            # Step 5: Wait 2 seconds, then filling email
            if not self.safe_wait(2):
                self.send_message_safe(
                    self.translations['messages']['filling_email'],
                    f'Filling email field... Email: {self.email}',
                    loop
                )
            
            # Step 6: Wait 5 seconds, then looking for password field
            if not self.safe_wait(5):
                self.send_message_safe(
                    self.translations['messages']['looking_password_field'],
                    'Looking for password field...',
                    loop
                )
            
            # Step 7: Wait 2 seconds, then filling password
            if not self.safe_wait(2):
                self.send_message_safe(
                    self.translations['messages']['filling_password'],
                    f'Filling password field... Password: {self.password}',
                    loop
                )
            
            # Step 8: Wait 5 seconds, then clicking login button
            if not self.safe_wait(5):
                self.send_message_safe(
                    self.translations['messages']['clicking_login'],
                    'Clicking login button...',
                    loop
                )
            
            # Step 9: Monitoring the game (immediately after login)
            if not self.stop_event.is_set():
                self.send_message_safe(
                    self.translations['messages']['monitoring_game'],
                    'Monitoring the game...',
                    loop
                )
            
            # Step 10: Main loop - send random results every 12 seconds
            while not self.stop_event.is_set() and self.is_running:
                try:
                    # Wait 12 seconds
                    if self.safe_wait(12):
                        break
                    
                    if not self.is_running or self.stop_event.is_set():
                        break
                    
                    # Generate and send random odds and result
                    odds_msg, result_msg = self.generate_random_result()
                    
                    # Send odds message
                    self.send_message_safe(odds_msg, f'Sent odds: {odds_msg}', loop)
                    
                    # Small delay between odds and result (1 second)
                    if self.safe_wait(1):
                        break
                    
                    if not self.is_running or self.stop_event.is_set():
                        break
                    
                    # Send result message
                    self.send_message_safe(result_msg, f'Sent result: {result_msg}', loop)
                    
                except Exception as e:
                    error_msg = f'Error in message loop iteration: {str(e)}'
                    self.log_message(error_msg)
                    print(f"Error in loop: {e}")
                    import traceback
                    traceback.print_exc()
                    # Wait a bit before continuing
                    if self.safe_wait(1):
                        break
            
            self.log_message('Message loop ended')
            print("Message loop ended")
            
        except Exception as e:
            error_msg = f'Fatal error in message_loop: {str(e)}'
            self.log_message(error_msg)
            print(f"Fatal error in message_loop: {e}")
            import traceback
            traceback.print_exc()
            # Update bot status if thread crashes
            self.is_running = False
            self.root.after(0, lambda: self.status_value.config(
                text=self.translations['status_stopped'],
                fg='#666666'
            ))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
        finally:
            # Clean up the event loop
            try:
                # Cancel all pending tasks
                pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
            except Exception as cleanup_error:
                print(f"Error cleaning up event loop: {cleanup_error}")
    
    def start_bot(self):
        """Start the bot simulation."""
        if not self.validate_inputs():
            return
        
        # Initialize bot
        try:
            self.bot = Bot(token=self.bot_token)
            self.is_running = True
            self.stop_event.clear()
            
            # Clear event loop reference
            self.message_loop_event_loop = None
            
            # Reset win/loss counters
            self.total_wins = 0
            self.total_losses = 0
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_value.config(
                text=self.translations['status_running'],
                fg='#4CAF50'
            )
            
            # Start message loop in background thread
            self.message_task = threading.Thread(target=self.message_loop, daemon=True)
            self.message_task.start()
            
            self.log_message('Bot initialization started')
            
        except Exception as e:
            messagebox.showerror(
                'Error',
                f"{self.translations['errors']['connection_error']}\n{str(e)}"
            )
            self.log_message(f'Failed to start bot: {str(e)}')
            self.is_running = False
    
    def stop_bot(self):
        """Stop the bot simulation."""
        self.is_running = False
        self.stop_event.set()
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_value.config(
            text=self.translations['status_stopped'],
            fg='#666666'
        )
        
        # Send stop message
        if self.bot:
            try:
                # Create a new event loop in a thread-safe way for the stop message
                def send_stop_message():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            new_loop.run_until_complete(self.send_telegram_message(self.translations['messages']['bot_stopped']))
                            self.log_message('Bot stopped - message sent')
                        finally:
                            new_loop.close()
                    except Exception as e:
                        self.log_message(f'Error sending stop message: {str(e)}')
                
                # Run in a separate thread to avoid blocking
                stop_thread = threading.Thread(target=send_stop_message, daemon=True)
                stop_thread.start()
            except Exception as e:
                self.log_message(f'Error creating stop message thread: {str(e)}')
        
        self.log_message('Bot stopped successfully')


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = BacBoBotController(root)
    
    # Handle window close
    def on_closing():
        if app.is_running:
            app.stop_bot()
        root.destroy()
    
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()


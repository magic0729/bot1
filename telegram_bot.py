import requests
import time

class TelegramBot:
    def __init__(self, token, channel_id, language='en'):
        self.token = token
        self.channel_id = channel_id
        self.language = language
        self.base_url = f"https://api.telegram.org/bot{token}"
        
        # Language translations
        self.translations = {
            'en': {
                'bot_started': '🤖 Bot started successfully!',
                'bot_stopped': '🛑 Bot stopped successfully!',
                'player': 'Player',
                'banker': 'Banker',
                'tie': 'Tie',
                'result': 'Result',
                'percentages': 'Percentages',
                'analysis': 'Analysis',
                'players_count': 'Players',
                'percentage': 'Percentage'
            },
            'pt': {
                'bot_started': '🤖 Bot iniciado com sucesso!',
                'bot_stopped': '🛑 Bot parado com sucesso!',
                'player': 'Jogador',
                'banker': 'Banqueiro',
                'tie': 'Empate',
                'result': 'Resultado',
                'percentages': 'Percentuais',
                'analysis': 'Análise',
                'players_count': 'Jogadores',
                'percentage': 'Percentual'
            }
        }
    
    def set_language(self, language):
        self.language = language
    
    def _get_text(self, key):
        return self.translations.get(self.language, self.translations['en']).get(key, key)
    
    def send_message(self, text, parse_mode='HTML'):
        """Send a message to Telegram channel with retries and extended timeout"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.channel_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
                return True
            except requests.exceptions.HTTPError as http_err:
                # Log and stop retrying for 400-level errors (likely formatting / bad chat id)
                print(f"Error sending Telegram message (HTTP): {http_err}")
                last_error = http_err
                if 400 <= response.status_code < 500:
                    break
            except Exception as e:
                print(f"Error sending Telegram message (attempt {attempt+1}/3): {e}")
                last_error = e
                time.sleep(1.5)
        return False
    
    def send_start_notification(self):
        """Send bot start notification"""
        message = self._get_text('bot_started')
        return self.send_message(message)
    
    def send_stop_notification(self):
        """Send bot stop notification"""
        message = self._get_text('bot_stopped')
        return self.send_message(message)
    
    def send_percentages(self, player_pct, banker_pct, tie_pct):
        """Send percentages message with colored formatting"""
        player_text = self._get_text('player')
        banker_text = self._get_text('banker')
        tie_text = self._get_text('tie')
        percentages_text = self._get_text('percentages')
        
        # Telegram does not support color styles; use colored emojis consistently
        message = f"📊 <b>{percentages_text}</b>\n\n"
        message += f"🟢 <b>{player_text}:</b> {player_pct}%\n"
        message += f"🔴 <b>{banker_text}:</b> {banker_pct}%\n"
        message += f"🔵 <b>{tie_text}:</b> {tie_pct}%"
        
        return self.send_message(message)
    
    def send_result(self, result_type):
        """Send game result (player/banker/tie)"""
        result_text = self._get_text('result')
        
        if result_type.lower() == 'player':
            player_text = self._get_text('player')
            message = f"🎯 <b>{result_text}:</b> 🟢 <b>{player_text}</b>"
        elif result_type.lower() == 'banker':
            banker_text = self._get_text('banker')
            message = f"🎯 <b>{result_text}:</b> 🔴 <b>{banker_text}</b>"
        elif result_type.lower() == 'tie':
            tie_text = self._get_text('tie')
            message = f"🎯 <b>{result_text}:</b> 🔵 <b>{tie_text}</b>"
        else:
            return False
        
        return self.send_message(message)
    
    def send_analysis(self, players_count, percentage):
        """Send analysis results"""
        analysis_text = self._get_text('analysis')
        players_count_text = self._get_text('players_count')
        percentage_text = self._get_text('percentage')
        
        message = f"📈 <b>{analysis_text}</b>\n\n"
        message += f"<b>{players_count_text}:</b> {players_count}\n"
        message += f"<b>{percentage_text}:</b> {percentage}%"
        
        return self.send_message(message)


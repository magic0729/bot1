from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import time
from bot_scraper import BotScraper
from telegram_bot import TelegramBot

app = Flask(__name__)
CORS(app)

# Global bot instance
bot_scraper = None
bot_thread = None
telegram_bot = None
is_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot_scraper, bot_thread, telegram_bot, is_running
    
    if is_running:
        return jsonify({'success': False, 'message': 'Bot is already running'}), 400
    
    data = request.json
    token = data.get('token')
    channel_id = data.get('channel_id')
    language = data.get('language', 'en')
    
    if not token or not channel_id:
        return jsonify({'success': False, 'message': 'Token and Channel ID are required'}), 400
    
    try:
        # Initialize Telegram bot
        telegram_bot = TelegramBot(token, channel_id, language)
        
        # Send start notification immediately when start button is clicked
        telegram_bot.send_start_notification()
        
        # Initialize and start scraper bot
        bot_scraper = BotScraper(telegram_bot, language)
        bot_thread = threading.Thread(target=bot_scraper.run, daemon=True)
        bot_thread.start()
        
        is_running = True
        return jsonify({'success': True, 'message': 'Bot started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot_scraper, bot_thread, is_running
    
    if not is_running:
        return jsonify({'success': False, 'message': 'Bot is not running'}), 400
    
    try:
        if bot_scraper:
            bot_scraper.stop()
        is_running = False
        # Wait a bit for cleanup
        if bot_thread and bot_thread.is_alive():
            bot_thread.join(timeout=5)
        return jsonify({'success': True, 'message': 'Bot stopped successfully'})
    except Exception as e:
        is_running = False
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({'running': is_running})

@app.route('/api/change-language', methods=['POST'])
def change_language():
    global bot_scraper, telegram_bot
    
    data = request.json
    language = data.get('language', 'en')
    
    if telegram_bot:
        telegram_bot.set_language(language)
    if bot_scraper:
        bot_scraper.set_language(language)
    
    return jsonify({'success': True, 'message': f'Language changed to {language}'})

if __name__ == '__main__':
    import sys
    import os
    # Get port from environment variable (Railway requirement) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Disable reloader on Windows and in production (Railway)
    use_reloader = sys.platform != 'win32' and os.environ.get('FLASK_ENV') != 'production'
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=use_reloader)


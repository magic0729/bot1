from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import hashlib
import os
import base64
import shutil
try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: easyocr not available. OCR-based percentage extraction disabled.")
from PIL import Image
import io

class BotScraper:
    def __init__(self, telegram_bot, language='en'):
        self.telegram_bot = telegram_bot
        self.language = language
        self.driver = None
        self.running = False
        self.url = "https://www.vemabet10.com/pt/game/bac-bo/play-for-real"
        # Manual login flow: credentials are not used
        self.email = None
        self.password = None
        self.last_result = None
        self.last_percentages = None
        self.last_analysis = None
        self.result_sent_for_round = False
        self.current_round_id = None
        self.data_file_path = os.path.join('data', 'scrape_results.csv')
        self._last_written_snapshot = None
        self.screenshot_dir = os.path.join('data', 'screenshots')
        self._last_screenshot_ts = 0.0
        self._last_percentage_sent_ts = 0.0
        self._ocr_reader = None
        if OCR_AVAILABLE:
            try:
                print("Initializing OCR reader...")
                self._ocr_reader = easyocr.Reader(['en', 'pt'], gpu=False)
                print("OCR reader initialized successfully!")
            except Exception as e:
                print(f"Warning: Failed to initialize OCR reader: {e}")
                self._ocr_reader = None
    
    def set_language(self, language):
        self.language = language
        if self.telegram_bot:
            self.telegram_bot.set_language(language)
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        # Enable headless mode in production (Railway/cloud environments)
        import os
        is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production'
        if is_production:
            chrome_options.add_argument('--headless=new')  # Use new headless mode
            print("Running in headless mode (production environment)")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # Additional options for Railway/cloud environments
        if is_production:
            chrome_options.add_argument('--single-process')  # May help in some cloud environments
            chrome_options.add_argument('--disable-setuid-sandbox')
            # Set Chrome binary path for Railway/Nixpacks
            import glob
            chrome_binary_paths = [
                '/nix/store/*/chromium-*/bin/chromium',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/usr/bin/google-chrome',
            ]
            for pattern in chrome_binary_paths:
                matches = glob.glob(pattern)
                if matches:
                    chrome_options.binary_location = matches[0]
                    print(f"Found Chrome at: {matches[0]}")
                    break
            
            # Set ChromeDriver path for Railway/Nixpacks
            chromedriver_paths = [
                '/nix/store/*/chromedriver-*/bin/chromedriver',
                '/usr/bin/chromedriver',
            ]
            for pattern in chromedriver_paths:
                matches = glob.glob(pattern)
                if matches:
                    os.environ['PATH'] = os.path.dirname(matches[0]) + os.pathsep + os.environ.get('PATH', '')
                    print(f"Found ChromeDriver at: {matches[0]}")
                    break
        
        # First, try to use system ChromeDriver (if available in PATH)
        try:
            print("Attempting to use system ChromeDriver...")
            self.driver = webdriver.Chrome(options=chrome_options)
            if not is_production:
                try:
                    self.driver.maximize_window()
                except:
                    pass  # Maximize may fail in headless mode
            self.driver.implicitly_wait(10)
            print("ChromeDriver setup successful using system driver!")
            return
        except Exception as e1:
            print(f"System ChromeDriver not available: {e1}")
            print("Trying to download ChromeDriver using webdriver-manager...")
        
        # Try to setup ChromeDriver with webdriver-manager
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to setup ChromeDriver (attempt {attempt + 1}/{max_retries})...")
                
                # Clear cache on retry
                if attempt > 0:
                    try:
                        cache_path = os.path.join(os.path.expanduser("~"), ".wdm")
                        if os.path.exists(cache_path):
                            print("Clearing ChromeDriver cache...")
                            shutil.rmtree(cache_path, ignore_errors=True)
                            time.sleep(1)
                    except Exception as e:
                        print(f"Warning: Could not clear cache: {e}")
                
                # Try to install ChromeDriver with cache clearing
                try:
                    driver_path = ChromeDriverManager().install()
                except Exception as install_error:
                    # If install fails, try clearing cache first
                    if attempt == 0:
                        try:
                            cache_path = os.path.join(os.path.expanduser("~"), ".wdm")
                            if os.path.exists(cache_path):
                                print("Clearing ChromeDriver cache due to install error...")
                                shutil.rmtree(cache_path, ignore_errors=True)
                                time.sleep(1)
                            driver_path = ChromeDriverManager().install()
                        except:
                            raise install_error
                    else:
                        raise install_error
                
                print(f"ChromeDriver installed at: {driver_path}")
                
                # Verify the driver file exists
                if not os.path.exists(driver_path):
                    raise FileNotFoundError(f"ChromeDriver not found at {driver_path}")
                
                # Verify it's a valid executable (check file extension on Windows)
                if os.name == 'nt' and not driver_path.endswith('.exe'):
                    # Try to find .exe version
                    exe_path = driver_path + '.exe'
                    if os.path.exists(exe_path):
                        driver_path = exe_path
                    else:
                        # Check if there's a chromedriver.exe in the same directory
                        dir_path = os.path.dirname(driver_path)
                        exe_path = os.path.join(dir_path, 'chromedriver.exe')
                        if os.path.exists(exe_path):
                            driver_path = exe_path
                
                # Create service and driver
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.maximize_window()
                self.driver.implicitly_wait(10)
                print("ChromeDriver setup successful!")
                return
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error setting up ChromeDriver (attempt {attempt + 1}): {error_msg}")
                
                # Check for specific WinError 193
                if "WinError 193" in error_msg or "not a valid Win32 application" in error_msg:
                    print("Detected Win32 compatibility issue. Clearing cache and retrying...")
                    try:
                        cache_path = os.path.join(os.path.expanduser("~"), ".wdm")
                        if os.path.exists(cache_path):
                            shutil.rmtree(cache_path, ignore_errors=True)
                            time.sleep(2)
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(2)
                else:
                    raise Exception(
                        f"Failed to setup ChromeDriver after {max_retries} attempts.\n"
                        f"Last error: {error_msg}\n"
                        f"Please ensure:\n"
                        f"1. Chrome browser is installed\n"
                        f"2. You have internet connection (for downloading ChromeDriver)\n"
                        f"3. Try manually downloading ChromeDriver from https://chromedriver.chromium.org/"
                    )
    
    def is_logged_in(self):
        """Heuristic check to determine if user is logged in."""
        try:
            # Indicators that suggest logged-in state
            logout_indicators = [
                "//*[contains(text(), 'Sair')]",
                "//*[contains(text(), 'Logout')]",
                "//*[contains(@class, 'logout')]",
                "//*[contains(@href, 'logout')]",
            ]
            for xp in logout_indicators:
                if self.driver.find_elements(By.XPATH, xp):
                    return True
            # Presence of balance/user/menu elements
            user_indicators = [
                "//*[contains(@class, 'balance')]",
                "//*[contains(@class, 'user')]",
                "//*[contains(@class, 'profile')]",
                "//*[contains(@id, 'balance')]",
            ]
            for xp in user_indicators:
                if self.driver.find_elements(By.XPATH, xp):
                    return True
        except:
            pass
        return False

    def wait_for_manual_login(self, timeout_seconds: int = 300) -> bool:
        """Open the site and wait for the user to complete login manually."""
        print("Navigating to website for manual login...")
        self.driver.get(self.url)
        start_time = time.time()
        # Notify user via Telegram once
        try:
            if self.telegram_bot:
                self.telegram_bot.send_message("⏳ Waiting for manual login... Please log in on the site, then the bot will start.")
        except Exception as e:
            print(f"Warning: could not send waiting message: {e}")
        # Poll until logged in or timeout
        while time.time() - start_time < timeout_seconds and self.running:
            if self.is_logged_in():
                print("Manual login detected.")
                try:
                    if self.telegram_bot:
                        self.telegram_bot.send_message("✅ Login detected. Starting monitoring.")
                except Exception as e:
                    print(f"Warning: could not send login detected message: {e}")
                # Save an initial screenshot after login
                try:
                    self._save_fullpage_screenshot(round_id="login", tag="after-login")
                except Exception as e:
                    print(f"Warning: could not save login screenshot: {e}")
                return True
            time.sleep(1)
        print("Manual login wait timed out.")
        return False

    def _ensure_data_file(self):
        try:
            os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
            if not os.path.exists(self.data_file_path):
                with open(self.data_file_path, 'w', encoding='utf-8') as f:
                    f.write('timestamp,round_id,player_pct,banker_pct,tie_pct,result,players_count,analysis_pct\n')
        except Exception as e:
            print(f"Error ensuring data file: {e}")

    def _save_record(self, round_id, player_pct, banker_pct, tie_pct, result, players_count, analysis_pct):
        try:
            self._ensure_data_file()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            # Avoid writing identical consecutive snapshots
            snapshot = (round_id, player_pct, banker_pct, tie_pct, result or '', players_count or '', analysis_pct or '')
            if snapshot == self._last_written_snapshot:
                return
            with open(self.data_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp},{round_id},{player_pct},{banker_pct},{tie_pct},{result or ''},{players_count or ''},{analysis_pct or ''}\n")
            self._last_written_snapshot = snapshot
        except Exception as e:
            print(f"Error saving record: {e}")

    def _ensure_screenshot_dir(self):
        try:
            os.makedirs(self.screenshot_dir, exist_ok=True)
        except Exception as e:
            print(f"Error ensuring screenshot dir: {e}")

    def _save_fullpage_screenshot(self, round_id: str, tag: str = "update"):
        """Capture and save a full-page PNG screenshot (full document height).
        Tries DevTools 'Page.captureScreenshot' with clip first, then falls back to window resize.
        """
        self._ensure_screenshot_dir()
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_round-{round_id}_{tag}.png"
        path = os.path.join(self.screenshot_dir, filename)

        # Attempt 1: DevTools with document clip
        try:
            try:
                self.driver.execute_cdp_cmd('Page.enable', {})
            except Exception:
                pass
            metrics = self.driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
            content = metrics.get('contentSize') or {}
            width = float(content.get('width', 1920))
            height = float(content.get('height', 1080))
            clip = { 'x': 0, 'y': 0, 'width': width, 'height': height, 'scale': 1 }
            screenshot = self.driver.execute_cdp_cmd('Page.captureScreenshot', {
                'format': 'png',
                'clip': clip,
                'fromSurface': True
            })
            data = screenshot.get('data')
            if data:
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(data))
                return
        except Exception as e:
            print(f"DevTools fullpage capture failed, will fallback: {e}")

        # Attempt 2: Resize window to full document height and use standard screenshot
        try:
            total_width = int(self.driver.execute_script('return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, document.documentElement.clientWidth);'))
            total_height = int(self.driver.execute_script('return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.documentElement.clientHeight);'))
            # Save current size
            current_size = self.driver.get_window_size()
            self.driver.set_window_size(total_width, total_height)
            # Allow layout to settle briefly
            time.sleep(0.05)
            self.driver.save_screenshot(path)
            # Restore previous size (avoid impacting scraping)
            self.driver.set_window_size(current_size.get('width', 1920), current_size.get('height', 1080))
        except Exception as e:
            print(f"Fallback fullpage screenshot failed: {e}")
    
    def extract_percentages(self):
        """Extract player, banker, and tie percentages from the horizontal bar graph using OCR"""
        try:
            # Method 0: Use OCR on screenshot (MOST RELIABLE!)
            if self._ocr_reader and self.driver:
                try:
                    # Small wait to ensure page has updated
                    time.sleep(0.1)
                    
                    # Take a FRESH screenshot - force refresh by scrolling slightly and back
                    try:
                        # Scroll to top to ensure we capture the bar graph area
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(0.05)
                    except:
                        pass
                    
                    # Take screenshot
                    screenshot = self.driver.execute_cdp_cmd(
                        'Page.captureScreenshot',
                        {
                            'format': 'png',
                            'fromSurface': True,
                            'captureBeyondViewport': True
                        }
                    )
                    png_b64 = screenshot.get('data')
                    if png_b64:
                        img_bytes = base64.b64decode(png_b64)
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # Crop to the bar graph area (typically top-right area)
                        width, height = img.size
                        print(f"Full screenshot size: {width}x{height}")
                        
                        # Try multiple crop areas to find the percentages
                        # Based on screenshots, the bar graph is in the top-right area
                        crop_areas = [
                            (int(width * 0.45), 0, width, int(height * 0.35)),  # Top-right 55% width, 35% height
                            (int(width * 0.5), 0, width, int(height * 0.4)),    # Top-right 50% width, 40% height
                            (int(width * 0.55), 0, width, int(height * 0.3)),   # Top-right 45% width, 30% height
                            (int(width * 0.4), 0, width, int(height * 0.5)),    # Top-right 60% width, 50% height
                        ]
                        
                        best_result = None
                        best_confidence_sum = 0
                        
                        for idx, crop_box in enumerate(crop_areas):
                            try:
                                cropped_img = img.crop(crop_box)
                                
                                # Save debug crop image occasionally
                                if idx == 0:  # Save first crop for debugging
                                    debug_path = os.path.join(self.screenshot_dir, f"debug_crop_{int(time.time())}.png")
                                    try:
                                        os.makedirs(self.screenshot_dir, exist_ok=True)
                                        cropped_img.save(debug_path)
                                        print(f"Debug: Saved crop area to {debug_path}")
                                    except:
                                        pass
                                
                                results = self._ocr_reader.readtext(cropped_img, detail=1)
                                
                                # Look for percentage patterns
                                pct_with_pos = []
                                all_text_found = []
                                
                                for (bbox, text, confidence) in results:
                                    all_text_found.append(f"{text}({confidence:.2f})")
                                    if confidence > 0.2:  # Lower threshold
                                        # Look for patterns like "52%", "8%", "52.5%", etc.
                                        matches = re.findall(r'(\d+\.?\d*)\s*%', text)
                                        for match in matches:
                                            try:
                                                value = float(match)
                                                if 0.5 <= value <= 100:  # Valid percentage range
                                                    # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                                                    x_center = (bbox[0][0] + bbox[2][0]) / 2
                                                    y_center = (bbox[0][1] + bbox[2][1]) / 2
                                                    pct_with_pos.append({
                                                        'value': value, 
                                                        'x': x_center, 
                                                        'y': y_center,
                                                        'confidence': confidence,
                                                        'text': text
                                                    })
                                            except ValueError:
                                                continue
                                
                                print(f"OCR crop {idx}: Found {len(pct_with_pos)} percentages. Text: {', '.join(all_text_found[:10])}")
                                
                                # If we found 3 or more percentages, try to identify them
                                if len(pct_with_pos) >= 3:
                                    # Sort by x position (left to right)
                                    pct_with_pos.sort(key=lambda x: x['x'])
                                    
                                    # Filter to get the best 3 (highest confidence, reasonable spacing)
                                    # Take percentages that are roughly on the same row
                                    if len(pct_with_pos) > 3:
                                        # Group by y position (same row)
                                        y_groups = {}
                                        for pct in pct_with_pos:
                                            y_key = round(pct['y'] / 15) * 15  # 15px tolerance
                                            if y_key not in y_groups:
                                                y_groups[y_key] = []
                                            y_groups[y_key].append(pct)
                                        
                                        # Find the group with 3 percentages
                                        best_group = None
                                        for y_key, group in y_groups.items():
                                            if len(group) >= 3:
                                                # Sort by confidence and take top 3
                                                group.sort(key=lambda x: x['confidence'], reverse=True)
                                                best_group = sorted(group[:3], key=lambda x: x['x'])
                                                break
                                        
                                        if best_group:
                                            pct_with_pos = best_group
                                        else:
                                            # Take first 3 by x position, but prefer higher confidence
                                            pct_with_pos.sort(key=lambda x: (x['confidence'], -x['x']), reverse=True)
                                            pct_with_pos = sorted(pct_with_pos[:3], key=lambda x: x['x'])
                                    
                                    if len(pct_with_pos) >= 3:
                                        # Calculate confidence sum
                                        conf_sum = sum(p['confidence'] for p in pct_with_pos)
                                        
                                        # Assign: left = Player, middle = Tie, right = Banker
                                        player_pct_val = round(pct_with_pos[0]['value'], 2)
                                        tie_pct_val = round(pct_with_pos[1]['value'], 2)
                                        banker_pct_val = round(pct_with_pos[2]['value'], 2)
                                        
                                        # Keep the best result (highest confidence)
                                        if conf_sum > best_confidence_sum:
                                            best_confidence_sum = conf_sum
                                            best_result = (player_pct_val, banker_pct_val, tie_pct_val)
                                            print(f"OCR crop {idx} - Best so far: P={player_pct_val}%, T={tie_pct_val}%, B={banker_pct_val}% (conf: {conf_sum:.2f})")
                            except Exception as e:
                                print(f"OCR error on crop area {idx}: {e}")
                                continue
                        
                        # Return best result if found
                        if best_result:
                            p, b, t = best_result
                            print(f"✅ OCR FINAL RESULT: P={p}%, T={t}%, B={b}%")
                            # Validate and return
                            p = max(0.0, min(100.0, float(p)))
                            b = max(0.0, min(100.0, float(b)))
                            t = max(0.0, min(100.0, float(t)))
                            return round(p, 2), round(b, 2), round(t, 2)
                        else:
                            print("⚠️ OCR found percentages but couldn't identify 3 valid ones")
                except Exception as e:
                    print(f"OCR extraction error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Fallback to DOM-based extraction if OCR fails
            percentage_pattern = r'(\d+\.?\d*)\s*%'
            
            player_pct = None
            banker_pct = None
            tie_pct = None
            
            # Method 1: Look for horizontal bar graph with percentages (DOM-based fallback)
            # The bar shows percentages like "52%", "8%", "40%" with "P O B O" labels below
            try:
                # Find all elements containing percentages
                all_pct_elements = self.driver.find_elements(By.XPATH, "//*[text()[contains(., '%')]]")
                
                # Look for a container that has 3 percentages together (the bar graph)
                # Usually these percentages are in the same parent or nearby elements
                pct_values_found = []
                for elem in all_pct_elements:
                    try:
                        text = elem.text.strip()
                        match = re.search(percentage_pattern, text)
                        if match:
                            value = float(match.group(1))
                            if 0 <= value <= 100:
                                # Get the parent container to check for P/B/T/O labels
                                try:
                                    parent = elem.find_element(By.XPATH, "..")
                                    grandparent = parent.find_element(By.XPATH, "..") if parent else None
                                    
                                    # Check if this container has P, B, T, O labels nearby
                                    container_text = ""
                                    try:
                                        container_text = parent.text
                                        if grandparent:
                                            container_text += " " + grandparent.text
                                    except:
                                        pass
                                    
                                    container_text_lower = container_text.lower()
                                    
                                    # Get location for sorting
                                    location = elem.location
                                    
                                    # Look for the pattern: percentages with P, O, B, O labels
                                    # The order is typically: Player %, Tie %, Banker %
                                    pct_values_found.append({
                                        'value': value,
                                        'elem': elem,
                                        'container': container_text_lower,
                                        'location': location,
                                        'text': text
                                    })
                                except:
                                    pass
                    except:
                        continue
                
                # If we found 3 or more percentages, try to match them to P/B/T
                if len(pct_values_found) >= 3:
                    # Sort by x position (left to right) - typically Player, Tie, Banker
                    pct_values_found.sort(key=lambda x: x['location']['x'])
                    
                    # Get all container text together to check for P/B/T indicators
                    all_container_text = " ".join([p['container'] for p in pct_values_found[:10]])  # Check first 10
                    
                    # Try to find which percentage corresponds to which
                    # Look for containers that have "p" or "jogador" near the first percentage
                    for i, pct_info in enumerate(pct_values_found[:10]):  # Check first 10 percentages
                        container = pct_info['container']
                        value = pct_info['value']
                        text = pct_info['text']
                        
                        # Check if this container or nearby has P/B/T indicators
                        # Also check siblings and nearby elements
                        if not player_pct:
                            if ('p' in container or 'jogador' in container or 'player' in container or 
                                (i == 0 and 'p' in all_container_text)):
                                player_pct = str(value)
                                continue
                        
                        if not banker_pct:
                            if ('b' in container or 'banqueiro' in container or 'banker' in container or 
                                'banca' in container or (i == 2 and 'b' in all_container_text)):
                                banker_pct = str(value)
                                continue
                        
                        if not tie_pct:
                            if ('t' in container or 'empate' in container or 'tie' in container or 
                                (i == 1 and ('o' in container or 't' in all_container_text))):
                                tie_pct = str(value)
                                continue
                    
                    # If we still don't have all three, use position-based assignment
                    # Based on screenshots: left = Player, middle = Tie, right = Banker
                    if not player_pct and len(pct_values_found) > 0:
                        player_pct = str(pct_values_found[0]['value'])
                    if not tie_pct and len(pct_values_found) > 1:
                        # Middle percentage is usually the smallest (Tie)
                        # Sort by value and take the middle one, or take index 1
                        sorted_by_value = sorted(pct_values_found[:3], key=lambda x: x['value'])
                        tie_pct = str(sorted_by_value[0]['value']) if len(sorted_by_value) > 0 else str(pct_values_found[1]['value'])
                    if not banker_pct and len(pct_values_found) > 2:
                        banker_pct = str(pct_values_found[2]['value'])
                    
                    # If we found all three, we're done
                    if player_pct and banker_pct and tie_pct:
                        print(f"Found percentages from bar graph: P={player_pct}%, T={tie_pct}%, B={banker_pct}%")
                        # Convert and return
                        try:
                            p = max(0.0, min(100.0, float(player_pct)))
                            b = max(0.0, min(100.0, float(banker_pct)))
                            t = max(0.0, min(100.0, float(tie_pct)))
                            return round(p, 2), round(b, 2), round(t, 2)
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                print(f"Error in bar graph method: {e}")

            # Method 0.5: Read widths of colored bars (blue=player, yellow=tie, red=banker)
            if not (player_pct and banker_pct and tie_pct):
                try:
                    js = """
                    const nodes = Array.from(document.querySelectorAll('*'));
                    const out = [];
                    for (const el of nodes) {
                      const cs = window.getComputedStyle(el);
                      const styleAttr = (el.getAttribute('style')||'').toLowerCase();
                      // Prefer inline width: NN%
                      let m = styleAttr.match(/width\s*:\s*(\d+(?:\.\d+)?)%/);
                      let pct = m ? parseFloat(m[1]) : null;
                      // If inline not present, try aria-valuenow or dataset value
                      if (pct === null) {
                        const aria = el.getAttribute('aria-valuenow');
                        if (aria && /^\d+(?:\.\d+)?$/.test(aria)) pct = parseFloat(aria);
                      }
                      // Some progress bars set width via CSS class; infer from bounding rect vs parent
                      if (pct === null) {
                        const p = el.parentElement;
                        if (p) {
                          const r = el.getBoundingClientRect();
                          const pr = p.getBoundingClientRect();
                          if (pr.width > 0 && r.width > 0 && pr.width >= r.width) {
                            const est = (r.width / pr.width) * 100;
                            if (est >= 0.5 && est <= 100.0) pct = est;
                          }
                        }
                      }
                      if (pct === null) continue;
                      const bg = cs.backgroundColor;
                      const rect = el.getBoundingClientRect();
                      out.push({ pct, bg, x: rect.x, y: rect.y, w: rect.width, h: rect.height });
                    }
                    return out;
                    """
                    candidates = self.driver.execute_script(js)
                    # Filter sensible bars (horizontal strips)
                    bars = [b for b in candidates if b and b.get('h', 0) <= 80 and b.get('w', 0) >= 40 and 0 <= b.get('pct', 0) <= 100]
                    # Group by similar y (on same row)
                    bars.sort(key=lambda b: (round(b['y']/5)*5, b['x']))
                    best_triplet = None
                    best_score = -1
                    for i in range(len(bars)):
                        for j in range(i+1, len(bars)):
                            for k in range(j+1, len(bars)):
                                trip = [bars[i], bars[j], bars[k]]
                                ys = [b['y'] for b in trip]
                                if max(ys) - min(ys) > 30:  # require roughly same row
                                    continue
                                trip_sorted = sorted(trip, key=lambda b: b['x'])
                                total = sum(b['pct'] for b in trip_sorted)
                                if 80 <= total <= 120:  # sum near 100
                                    score = 120 - abs(100-total)
                                    if score > best_score:
                                        best_score = score
                                        best_triplet = trip_sorted
                    if best_triplet:
                        # Map by color heuristic: blue=player, red=banker, yellow/orange=tie
                        def classify(b):
                            bg = (b.get('bg') or '').lower()
                            # Extract rgb numbers
                            import re as _re
                            m = _re.search(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', bg)
                            r, g, bl = (0,0,0)
                            if m:
                                r, g, bl = int(m.group(1)), int(m.group(2)), int(m.group(3))
                            # Heuristics
                            if bl > r and bl > g:
                                return 'player'
                            if r > bl and r >= g:
                                return 'banker'
                            if g >= 80 and r >= 80 and bl < 120:
                                return 'tie'
                            return 'unknown'
                        mapping = { classify(b): b['pct'] for b in best_triplet }
                        # Fallback by position if any unknowns
                        left, mid, right = best_triplet
                        if 'player' not in mapping:
                            mapping['player'] = left['pct']
                        if 'tie' not in mapping:
                            mapping['tie'] = mid['pct']
                        if 'banker' not in mapping:
                            mapping['banker'] = right['pct']
                        player_pct = str(round(mapping.get('player', 0.0), 2))
                        banker_pct = str(round(mapping.get('banker', 0.0), 2))
                        tie_pct = str(round(mapping.get('tie', 0.0), 2))
                except Exception as e:
                    print(f"Error in bar width method: {e}")
            
            # Method 1: Look for percentages near roadmap/statistics area (most reliable)
            # Look for percentages that appear near P, B, T indicators or in statistics sections
            try:
                # Find roadmap/statistics containers
                roadmap_selectors = [
                    "//*[contains(@class, 'roadmap')]",
                    "//*[contains(@class, 'statistics')]",
                    "//*[contains(@class, 'stats')]",
                    "//*[contains(@id, 'roadmap')]",
                    "//*[contains(@id, 'statistics')]",
                    "//*[contains(@class, 'history')]",
                ]
                
                for selector in roadmap_selectors:
                    try:
                        containers = self.driver.find_elements(By.XPATH, selector)
                        for container in containers:
                            # Look for percentages within this container
                            pct_elements = container.find_elements(By.XPATH, ".//*[text()[contains(., '%')]]")
                            for elem in pct_elements:
                                try:
                                    text = elem.text.strip()
                                    # Get surrounding context
                                    parent = elem.find_element(By.XPATH, "..")
                                    parent_text = parent.text.lower()
                                    
                                    # Look for P/B/T indicators nearby
                                    # Check if there's a P, B, or T icon/text near this percentage
                                    siblings = parent.find_elements(By.XPATH, "./*")
                                    context_text = " ".join([s.text.lower() for s in siblings if s.text]).lower()
                                    
                                    match = re.search(percentage_pattern, text)
                                    if match:
                                        value = float(match.group(1))
                                        # Check context to determine which percentage this is
                                        if ('p' in context_text or 'player' in context_text or 'jogador' in context_text) and not player_pct:
                                            player_pct = str(value)
                                        elif ('b' in context_text or 'banker' in context_text or 'banqueiro' in context_text or 'banca' in context_text) and not banker_pct:
                                            banker_pct = str(value)
                                        elif ('t' in context_text or 'tie' in context_text or 'empate' in context_text) and not tie_pct:
                                            tie_pct = str(value)
                                except:
                                    continue
                    except:
                        continue
            except Exception as e:
                print(f"Error in roadmap method: {e}")
            
            # Method 2: Look for percentages in a row/sequence (common pattern: P%, B%, T%)
            if not all([player_pct, banker_pct, tie_pct]):
                try:
                    # Find elements containing percentages and look for patterns
                    all_pct_elements = self.driver.find_elements(By.XPATH, "//*[text()[contains(., '%')]]")
                    pct_values = []
                    for elem in all_pct_elements:
                        try:
                            text = elem.text.strip()
                            match = re.search(percentage_pattern, text)
                            if match:
                                value = float(match.group(1))
                                # Only consider reasonable percentages (0-100)
                                if 0 <= value <= 100:
                                    # Get parent and siblings for context
                                    try:
                                        parent = elem.find_element(By.XPATH, "..")
                                        siblings = parent.find_elements(By.XPATH, "./*")
                                        all_text = " ".join([s.text for s in siblings if s.text]).lower()
                                        
                                        # Check for P/B/T indicators
                                        if 'p' in all_text or 'player' in all_text or 'jogador' in all_text:
                                            if not player_pct:
                                                player_pct = str(value)
                                        elif 'b' in all_text or 'banker' in all_text or 'banqueiro' in all_text or 'banca' in all_text:
                                            if not banker_pct:
                                                banker_pct = str(value)
                                        elif 't' in all_text or 'tie' in all_text or 'empate' in all_text:
                                            if not tie_pct:
                                                tie_pct = str(value)
                                    except:
                                        pass
                        except:
                            continue
                except Exception as e:
                    print(f"Error in sequence method: {e}")
            
            # Method 3: Look for three percentages in close proximity (likely the win percentages)
            if not all([player_pct, banker_pct, tie_pct]):
                try:
                    # Find all percentage text nodes
                    all_elements = self.driver.find_elements(By.XPATH, "//*[text()[contains(., '%')]]")
                    pct_candidates = []
                    
                    for elem in all_elements:
                        try:
                            text = elem.text.strip()
                            match = re.search(percentage_pattern, text)
                            if match:
                                value = float(match.group(1))
                                if 0 <= value <= 100:
                                    # Get element location and surrounding text
                                    location = elem.location
                                    parent = elem.find_element(By.XPATH, "..")
                                    context = parent.text.lower()
                                    pct_candidates.append({
                                        'value': value,
                                        'context': context,
                                        'elem': elem
                                    })
                        except:
                            continue
                    
                    # If we found 3 percentages close together, they're likely P, B, T
                    if len(pct_candidates) >= 3:
                        # Sort by value or position
                        pct_candidates.sort(key=lambda x: x['value'])
                        # Try to match based on typical patterns
                        # Usually: Player is first, Banker is second, Tie is third (or vice versa)
                        if not player_pct and len(pct_candidates) > 0:
                            player_pct = str(pct_candidates[0]['value'])
                        if not banker_pct and len(pct_candidates) > 1:
                            banker_pct = str(pct_candidates[1]['value'])
                        if not tie_pct and len(pct_candidates) > 2:
                            tie_pct = str(pct_candidates[2]['value'])
                except Exception as e:
                    print(f"Error in proximity method: {e}")
            
            # Method 4: Look for percentages displayed with P/B/T icons (most common pattern)
            # This is typically shown above or near the roadmap grids
            if not all([player_pct, banker_pct, tie_pct]):
                try:
                    # Look for elements that contain both icons (P/B/T) and percentages
                    # Common pattern: "50% P" or "P 50%" or similar
                    icon_patterns = [
                        "//*[contains(text(), 'P') and contains(text(), '%')]",
                        "//*[contains(text(), 'B') and contains(text(), '%')]",
                        "//*[contains(text(), 'T') and contains(text(), '%')]",
                    ]
                    
                    for pattern in icon_patterns:
                        try:
                            elements = self.driver.find_elements(By.XPATH, pattern)
                            for elem in elements:
                                text = elem.text
                                # Look for percentage in this element or nearby
                                match = re.search(percentage_pattern, text)
                                if match:
                                    value = float(match.group(1))
                                    if 0 <= value <= 100:
                                        if 'P' in text and not player_pct:
                                            player_pct = str(value)
                                        elif 'B' in text and not banker_pct:
                                            banker_pct = str(value)
                                        elif 'T' in text and not tie_pct:
                                            tie_pct = str(value)
                        except:
                            continue
                    
                    # Also check parent containers for grouped percentages
                    try:
                        # Look for containers that have multiple percentages together
                        containers_with_pct = self.driver.find_elements(By.XPATH, "//*[count(.//*[contains(text(), '%')]) >= 2]")
                        for container in containers_with_pct:
                            container_text = container.text
                            # Extract all percentages from this container
                            pct_matches = re.findall(percentage_pattern, container_text)
                            if len(pct_matches) >= 3:
                                # Check if container has P/B/T indicators
                                if any(c in container_text.upper() for c in ['P', 'B', 'T', 'PLAYER', 'BANKER', 'TIE']):
                                    # Try to match percentages to P/B/T based on order or context
                                    values = [float(v) for v in pct_matches[:3] if 0 <= float(v) <= 100]
                                    if len(values) == 3:
                                        # Check order - typically shown as P, B, T or in that area
                                        if not player_pct:
                                            player_pct = str(values[0])
                                        if not banker_pct:
                                            banker_pct = str(values[1])
                                        if not tie_pct:
                                            tie_pct = str(values[2])
                                        break
                    except:
                        pass
                except Exception as e:
                    print(f"Error in icon method: {e}")
            
            # Default values if not found
            if not player_pct:
                player_pct = "0"
            if not banker_pct:
                banker_pct = "0"
            if not tie_pct:
                tie_pct = "0"

            # Convert and sanitize
            p = max(0.0, min(100.0, float(player_pct)))
            b = max(0.0, min(100.0, float(banker_pct)))
            t = max(0.0, min(100.0, float(tie_pct)))
            total = p + b + t
            
            # Debug: Print what we extracted
            if p > 0 or b > 0 or t > 0:
                print(f"Extracted percentages - Player: {p}%, Banker: {b}%, Tie: {t}% (Total: {total}%)")
            
            if total > 100.0 and total > 0.0:
                scale = 100.0 / total
                p = round(p * scale, 2)
                b = round(b * scale, 2)
                t = round(t * scale, 2)
                print(f"Normalized percentages - Player: {p}%, Banker: {b}%, Tie: {t}%")
            else:
                p = round(p, 2)
                b = round(b, 2)
                t = round(t, 2)
            return p, b, t
            
        except Exception as e:
            print(f"Error extracting percentages: {e}")
            return 0.0, 0.0, 0.0
    
    def extract_result(self):
        """Extract game result (player/banker/tie) by detecting victory banners"""
        try:
            # Method 1: Look for victory banners - "VITÓRIA DO JOGADOR", "VITÓRIA DA BANCA", etc.
            # These are displayed as large banners on the screen
            try:
                # Look for all text elements that might contain victory messages
                all_text_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                
                for elem in all_text_elements:
                    try:
                        text = elem.text.strip().upper()
                        # Check for Player win
                        if 'VITÓRIA DO JOGADOR' in text or 'VITÓRIA DO PLAYER' in text or 'VITÓRIA JOGADOR' in text:
                            # Verify it's visible (not hidden)
                            if elem.is_displayed():
                                print("Detected Player win from victory banner")
                                return 'player'
                        # Check for Banker win
                        elif 'VITÓRIA DA BANCA' in text or 'VITÓRIA DO BANQUEIRO' in text or 'VITÓRIA DA BANKER' in text or 'VITÓRIA BANCA' in text:
                            if elem.is_displayed():
                                print("Detected Banker win from victory banner")
                                return 'banker'
                        # Check for Tie
                        elif 'VITÓRIA DO EMPATE' in text or 'VITÓRIA EMPATE' in text:
                            if elem.is_displayed():
                                print("Detected Tie from victory banner")
                                return 'tie'
                    except:
                        continue
            except Exception as e:
                print(f"Error checking victory banners: {e}")
            
            # Also check page source as fallback
            try:
                page_source = self.driver.page_source.upper()
                if 'VITÓRIA DO JOGADOR' in page_source or 'VITÓRIA DO PLAYER' in page_source:
                    print("Detected Player win from page source")
                    return 'player'
                elif 'VITÓRIA DA BANCA' in page_source or 'VITÓRIA DO BANQUEIRO' in page_source:
                    print("Detected Banker win from page source")
                    return 'banker'
                elif 'VITÓRIA DO EMPATE' in page_source:
                    print("Detected Tie from page source")
                    return 'tie'
            except:
                pass
            
            # Method 2: Look for result elements by class/id
            result_keywords = ['result', 'winner', 'win', 'outcome', 'game-result', 'last-result', 'round-result', 'victory', 'vitória']
            for keyword in result_keywords:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(@class, '{keyword}') or contains(@id, '{keyword}')]")
                    for elem in elements:
                        try:
                            # Check text content
                            text = elem.text.lower()
                            if 'player' in text or 'jogador' in text:
                                # Verify it's a win result
                                if 'win' in text or 'ganhou' in text or 'won' in text or 'vitória' in text:
                                    return 'player'
                            elif 'banker' in text or 'banqueiro' in text or 'banca' in text:
                                if 'win' in text or 'ganhou' in text or 'won' in text or 'vitória' in text:
                                    return 'banker'
                            elif 'tie' in text or 'empate' in text:
                                if 'win' in text or 'ganhou' in text or 'won' in text or 'vitória' in text:
                                    return 'tie'
                            
                            # Check by color/style
                            style = elem.get_attribute('style') or ''
                            class_name = elem.get_attribute('class') or ''
                            
                            # Green indicates player win
                            if 'green' in style.lower() or 'green' in class_name.lower() or '#00ff00' in style or 'rgb(0, 255, 0)' in style:
                                if 'player' in text or 'jogador' in text:
                                    return 'player'
                            
                            # Red indicates banker win
                            if 'red' in style.lower() or 'red' in class_name.lower() or '#ff0000' in style or 'rgb(255, 0, 0)' in style:
                                if 'banker' in text or 'banqueiro' in text:
                                    return 'banker'
                            
                            # Dark blue indicates tie
                            if 'blue' in style.lower() or '#000080' in style or 'rgb(0, 0, 128)' in style:
                                if 'tie' in text or 'empate' in text:
                                    return 'tie'
                        except:
                            continue
                except:
                    continue
            
            # Method 2: Look for recent game history or result indicators
            try:
                # Look for elements that might show the latest result
                history_selectors = [
                    "//*[contains(@class, 'history')]",
                    "//*[contains(@class, 'recent')]",
                    "//*[contains(@class, 'last')]",
                    "//*[contains(@class, 'current')]"
                ]
                
                for selector in history_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements[:5]:  # Check first 5 elements
                            text = elem.text.lower()
                            html = elem.get_attribute('innerHTML') or ''
                            
                            # Check for player win indicators
                            if any(ind in text or ind in html for ind in ['player win', 'jogador ganhou', 'player won']):
                                return 'player'
                            
                            # Check for banker win indicators
                            if any(ind in text or ind in html for ind in ['banker win', 'banqueiro ganhou', 'banker won']):
                                return 'banker'
                            
                            # Check for tie indicators
                            if any(ind in text or ind in html for ind in ['tie', 'empate', 'draw']):
                                return 'tie'
                    except:
                        continue
            except:
                pass
            
            # Method 3: Check page source for result patterns
            try:
                page_source = self.driver.page_source.lower()
                
                # Look for result patterns
                if 'player' in page_source and ('win' in page_source or 'won' in page_source or 'ganhou' in page_source):
                    # Check if it's recent (near result keywords)
                    result_index = page_source.find('result')
                    player_index = page_source.find('player')
                    if result_index != -1 and player_index != -1 and abs(result_index - player_index) < 500:
                        return 'player'
                
                if 'banker' in page_source and ('win' in page_source or 'won' in page_source or 'ganhou' in page_source):
                    result_index = page_source.find('result')
                    banker_index = page_source.find('banker')
                    if result_index != -1 and banker_index != -1 and abs(result_index - banker_index) < 500:
                        return 'banker'
                
                if 'tie' in page_source or 'empate' in page_source:
                    result_index = page_source.find('result')
                    tie_index = page_source.find('tie') if 'tie' in page_source else page_source.find('empate')
                    if result_index != -1 and tie_index != -1 and abs(result_index - tie_index) < 500:
                        return 'tie'
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"Error extracting result: {e}")
            return None
    
    def extract_analysis(self):
        """Extract analysis data (players count and percentage)"""
        try:
            # Look for analysis section at bottom center
            page_source = self.driver.page_source
            
            # Try to find analysis elements
            analysis_patterns = [
                r'(\d+)\s*(?:players?|jogadores?)',
                r'players?[:\s]+(\d+)',
                r'jogadores?[:\s]+(\d+)'
            ]
            
            players_count = None
            percentage = None
            
            for pattern in analysis_patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    players_count = match.group(1)
                    break
            
            # Look for percentage in analysis area
            percentage_match = re.search(r'(\d+\.?\d*)\s*%', page_source)
            if percentage_match:
                percentage = percentage_match.group(1)
            
            return players_count, percentage
            
        except Exception as e:
            print(f"Error extracting analysis: {e}")
            return None, None
    
    def get_round_id(self):
        """Get a unique identifier for the current game round"""
        try:
            # Try to get a round identifier from the page
            # This could be a timestamp, round number, or game ID
            page_source = self.driver.page_source
            # Look for round identifiers
            round_patterns = [
                r'round[:\s]+(\d+)',
                r'game[:\s]+(\d+)',
                r'round["\']?\s*[:=]\s*["\']?(\d+)',
            ]
            for pattern in round_patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    return match.group(1)
            # Fallback: use page source hash as round ID
            return hashlib.md5(page_source[:1000].encode()).hexdigest()[:10]
        except:
            return str(time.time())
    
    def monitor_game(self):
        """Monitor the game and send updates"""
        try:
            # Check if we're in a new round
            round_id = self.get_round_id()
            is_new_round = (round_id != self.current_round_id)
            
            if is_new_round:
                self.current_round_id = round_id
                self.result_sent_for_round = False
                self.last_result = None
            
            # Extract percentages - ALWAYS get fresh data
            print(f"[{time.strftime('%H:%M:%S')}] Extracting percentages from fresh screenshot...")
            player_pct, banker_pct, tie_pct = self.extract_percentages()
            current_percentages = (round(player_pct, 2), round(banker_pct, 2), round(tie_pct, 2))
            
            print(f"[{time.strftime('%H:%M:%S')}] Extracted: P={player_pct:.2f}%, B={banker_pct:.2f}%, T={tie_pct:.2f}%")
            if self.last_percentages:
                print(f"[{time.strftime('%H:%M:%S')}] Previous: P={self.last_percentages[0]:.2f}%, B={self.last_percentages[1]:.2f}%, T={self.last_percentages[2]:.2f}%")
            
            # Send percentages every 10 seconds (regardless of changes)
            now_ts = time.time()
            should_send_pct = False
            time_since_last = now_ts - self._last_percentage_sent_ts
            if time_since_last >= 10.0:
                should_send_pct = True
                self._last_percentage_sent_ts = now_ts
                print(f"[{time.strftime('%H:%M:%S')}] ⏰ 10 seconds elapsed - sending percentages")
            
            # Also send if percentages changed significantly (more than 0.5%)
            pct_changed = False
            if self.last_percentages is None:
                pct_changed = True
                print(f"[{time.strftime('%H:%M:%S')}] First extraction - sending percentages")
            else:
                changes = [
                    abs(current_percentages[i] - self.last_percentages[i]) 
                    for i in range(3)
                ]
                max_change = max(changes)
                if max_change > 0.5:  # Increased threshold to 0.5% to avoid noise
                    pct_changed = True
                    print(f"[{time.strftime('%H:%M:%S')}] 📊 Percentages changed by {max_change:.2f}% - sending update")
            
            if should_send_pct or pct_changed:
                print(f"[{time.strftime('%H:%M:%S')}] 📤 Sending to Telegram: P={player_pct:.2f}%, B={banker_pct:.2f}%, T={tie_pct:.2f}%")
                self.telegram_bot.send_percentages(
                    f"{player_pct:.2f}",
                    f"{banker_pct:.2f}",
                    f"{tie_pct:.2f}"
                )
                self.last_percentages = current_percentages
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⏭️ Skipping send (no significant change, {time_since_last:.1f}s since last)")
            
            # Extract and send result (only once per round)
            if not self.result_sent_for_round:
                result = self.extract_result()
                if result and result != self.last_result:
                    self.telegram_bot.send_result(result)
                    self.last_result = result
                    self.result_sent_for_round = True
            
            # Extract and send analysis
            players_count, percentage = self.extract_analysis()
            if players_count and percentage:
                current_analysis = (players_count, percentage)
                if current_analysis != self.last_analysis:
                    self.telegram_bot.send_analysis(players_count, percentage)
                    self.last_analysis = current_analysis
            
            # Persist snapshot when anything changed
            if pct_changed or self.result_sent_for_round or (players_count and percentage):
                self._save_record(
                    round_id=round_id,
                    player_pct=f"{player_pct:.2f}",
                    banker_pct=f"{banker_pct:.2f}",
                    tie_pct=f"{tie_pct:.2f}",
                    result=self.last_result,
                    players_count=players_count,
                    analysis_pct=percentage,
                )
                # Save full-page screenshot for this update
                self._save_fullpage_screenshot(round_id=round_id, tag="update")

        except Exception as e:
            print(f"Error monitoring game: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main bot loop"""
        self.running = True
        
        try:
            # Setup driver
            self.setup_driver()
            
            # Manual login flow: wait for user to log in
            if not self.wait_for_manual_login(timeout_seconds=300):
                print("Login not detected within timeout.")
                try:
                    if self.telegram_bot:
                        self.telegram_bot.send_message("❌ Login not detected within timeout. Please restart and log in quickly.")
                except:
                    pass
                return
            
            # Start monitoring immediately after login
            print("Starting monitoring immediately after login...")
            
            # Initialize screenshot timestamp to trigger first screenshot immediately
            self._last_screenshot_ts = time.time() - 1.0
            # Initialize percentage send timestamp to send immediately
            self._last_percentage_sent_ts = time.time() - 10.0
            
            # Monitor game loop
            while self.running:
                try:
                    # Save full-page screenshot every 1 second (independent of monitor_game)
                    now_ts = time.time()
                    if now_ts - self._last_screenshot_ts >= 1.0:
                        try:
                            round_id = self.current_round_id or "unknown"
                            self._save_fullpage_screenshot(round_id=round_id, tag="tick")
                            self._last_screenshot_ts = now_ts
                            print(f"Screenshot saved: {time.strftime('%Y%m%d_%H%M%S')}_round-{round_id}_tick.png")
                        except Exception as e:
                            print(f"Warning: periodic screenshot failed: {e}")
                    
                    # Monitor game (scraping and sending updates)
                    self.monitor_game()
                    
                    time.sleep(0.5)  # Faster checks for near real-time updates
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(2)
            
        except Exception as e:
            print(f"Error in bot run: {e}")
            if self.telegram_bot:
                self.telegram_bot.send_message(f"❌ Bot error: {str(e)}")
        finally:
            self.cleanup()
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        try:
            if self.telegram_bot:
                self.telegram_bot.send_stop_notification()
        except Exception as e:
            print(f"Error sending stop notification: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            print(f"Error cleaning up: {e}")


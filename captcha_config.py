# captcha_config.py
# Configuration file for captcha bypass strategies

import os
from dotenv import load_dotenv

load_dotenv()

# --- Captcha Bypass Configuration ---

# Enable/disable different strategies
ENABLE_USER_AGENT_ROTATION = True
ENABLE_HUMAN_LIKE_DELAYS = True
ENABLE_STEALTH_MODE = True
ENABLE_PROXY_ROTATION = False  # Set to True if you have proxies

# User agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"
]

# Delay configuration (in seconds)
MIN_DELAY_BETWEEN_QUERIES = 3
MAX_DELAY_BETWEEN_QUERIES = 8
MIN_DELAY_BETWEEN_PAGES = 2
MAX_DELAY_BETWEEN_PAGES = 5

# Captcha handling configuration
CAPTCHA_TIMEOUT = 120  # seconds to wait for manual captcha solving
MAX_CAPTCHA_RETRIES = 3
ENABLE_AUTO_RETRY = True

# Proxy configuration (if you have proxies)
PROXY_LIST = [
    # Add your proxy URLs here
    # "http://username:password@proxy1.com:8080",
    # "http://username:password@proxy2.com:8080",
    # "socks5://username:password@proxy3.com:1080"
]

# Browser fingerprinting evasion
STEALTH_OPTIONS = {
    "disable_webdriver": True,
    "fake_plugins": True,
    "fake_languages": True,
    "fake_chrome": True,
    "fake_permissions": True
}

# Search strategy fallbacks
SEARCH_FALLBACKS = [
    "bing.com",
    "duckduckgo.com",
    "yandex.com"
]

# Rate limiting
MAX_REQUESTS_PER_HOUR = 50
MAX_REQUESTS_PER_DAY = 200

# --- Environment Variables ---
def get_proxy_url():
    """Get proxy URL from environment or rotate through list"""
    env_proxy = os.getenv("PROXY_URL")
    if env_proxy:
        return env_proxy
    
    if PROXY_LIST and ENABLE_PROXY_ROTATION:
        import random
        return random.choice(PROXY_LIST)
    
    return None

def get_user_agent():
    """Get user agent with rotation if enabled"""
    if ENABLE_USER_AGENT_ROTATION:
        import random
        return random.choice(USER_AGENTS)
    return USER_AGENTS[0]

# --- Captcha Detection Patterns ---
CAPTCHA_PATTERNS = [
    # Google reCAPTCHA
    "//iframe[contains(@src, 'recaptcha')]",
    "//div[contains(@class, 'recaptcha')]",
    "//div[contains(@class, 'g-recaptcha')]",
    
    # Google unusual activity
    "//div[contains(text(), 'unusual activity')]",
    "//div[contains(text(), 'verify you')]",
    "//div[contains(text(), 'robot')]",
    "//div[contains(text(), 'suspicious')]",
    
    # Other captcha systems
    "//div[contains(@class, 'captcha')]",
    "//img[contains(@src, 'captcha')]",
    "//form[contains(@action, 'captcha')]"
]

# --- Success Indicators ---
SUCCESS_INDICATORS = [
    "//div[contains(@class, 'g')]",  # Google search results
    "//div[contains(@class, 'result')]",  # Search results
    "//h3[contains(@class, 'LC20lb')]",  # Google result titles
    "//a[contains(@href, 'linkedin.com')]",  # LinkedIn links
    "//a[contains(@href, 'twitter.com')]"   # Twitter links
]

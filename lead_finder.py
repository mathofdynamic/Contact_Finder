#!/usr/bin/env python3
# lead_finder.py

import os
import json
import time
import random
from playwright.sync_api import sync_playwright, Page, BrowserContext
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Get cookie paths from .env file, using the same names as my existing files
GOOGLE_COOKIES_PATH = os.getenv("GOOGLE_COOKIES_PATH", "google-cookie.json")
# Add a placeholder for LinkedIn cookies, as they will be essential for scraping profiles
LINKEDIN_COOKIES_PATH = os.getenv("LINKEDIN_COOKIES_PATH", "linkedin_cookies.json") 

# --- Captcha Bypass Strategies ---

# Rotate user agents to appear more human-like
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# Add random delays to mimic human behavior
def human_like_delay():
    """Add random delays to mimic human behavior"""
    base_delay = random.uniform(2, 5)
    time.sleep(base_delay)

def handle_captcha_and_consent(page: Page) -> bool:
    """Handle Google captcha challenges and cookie consent dialogs"""
    print("🔍 Checking for captcha or consent dialogs...")
    
    # First, try to handle cookie consent dialogs
    if handle_cookie_consent(page):
        print("✅ Cookie consent handled successfully!")
    
    # Then check for captchas
    captcha_indicators = [
        "//iframe[contains(@src, 'recaptcha')]",
        "//div[contains(@class, 'recaptcha')]",
        "//div[contains(text(), 'unusual activity')]",
        "//div[contains(text(), 'verify you')]",
        "//div[contains(text(), 'robot')]"
    ]
    
    captcha_found = False
    for indicator in captcha_indicators:
        try:
            if page.locator(indicator).count() > 0:
                captcha_found = True
                break
        except:
            continue
    
    if not captcha_found:
        # Check for other captcha-like elements
        try:
            if "unusual activity" in page.content().lower() or "verify" in page.content().lower():
                captcha_found = True
        except:
            pass
    
    if captcha_found:
        print("🔒 Captcha challenge detected!")
        print("📋 Available options:")
        print("1. Manual solving (recommended)")
        print("2. Wait and retry")
        print("3. Use different search strategy")
        
        # Option 1: Manual solving
        print("\n🔄 Switching to manual mode...")
        print("Please solve the captcha manually in the browser window.")
        print("The script will wait for you to complete it...")
        
        # Wait for user to solve captcha manually
        print("⏰ Waiting up to 2 minutes for you to solve the captcha...")
        try:
            # Wait for captcha to be solved (look for search results)
            page.wait_for_selector('div.g', timeout=120000)  # 2 minutes timeout
            print("✅ Captcha appears to be solved! Continuing...")
            return True
        except Exception as e:
            print("⏰ Timeout waiting for captcha solution.")
            print("💡 Tip: Make sure to complete the captcha and wait for search results to appear.")
            return False
    
    return True

def handle_cookie_consent(page: Page) -> bool:
    """Handle Google cookie consent dialogs automatically"""
    try:
        # Wait a moment for the page to load
        page.wait_for_timeout(2000)
        
        # Common cookie consent button selectors
        consent_selectors = [
            # Accept all buttons
            "button[aria-label*='Accept all']",
            "button:has-text('Accept all')",
            "button:has-text('Alles accepteren')",  # Dutch
            "button:has-text('Alle akzeptieren')",  # German
            "button:has-text('Tout accepter')",     # French
            "button:has-text('Aceptar todo')",      # Spanish
            "button:has-text('Accetta tutto')",     # Italian
            
            # Accept buttons (without "all")
            "button[aria-label*='Accept']",
            "button:has-text('Accept')",
            "button:has-text('Akzeptieren')",
            "button:has-text('Accepter')",
            "button:has-text('Aceptar')",
            "button:has-text('Accetta')",
            
            # Generic accept patterns
            "button[data-identifier*='accept']",
            "button[id*='accept']",
            "button[class*='accept']",
            
            # Language switcher (if needed)
            "button:has-text('Change to English')",
            "button:has-text('English')",
            "a:has-text('English')"
        ]
        
        # Try to find and click consent buttons
        for selector in consent_selectors:
            try:
                if page.locator(selector).count() > 0:
                    print(f"🎯 Found consent button: {selector}")
                    page.locator(selector).first.click()
                    print("✅ Clicked consent button!")
                    
                    # Wait for the dialog to disappear
                    page.wait_for_timeout(2000)
                    return True
            except Exception as e:
                continue
        
        # If no buttons found, try to find by text content
        page_content = page.content().lower()
        if any(phrase in page_content for phrase in ['cookie', 'consent', 'privacy', 'accept', 'akzeptieren', 'accepter']):
            print("🔍 Cookie consent dialog detected, attempting to handle...")
            
            # Try clicking any button that might be an accept button
            buttons = page.locator('button').all()
            for button in buttons:
                try:
                    button_text = button.inner_text().lower()
                    if any(word in button_text for word in ['accept', 'ok', 'yes', 'continue', 'akzeptieren', 'accepter']):
                        print(f"🎯 Clicking button: {button_text}")
                        button.click()
                        page.wait_for_timeout(2000)
                        return True
                except:
                    continue
        
        return False
        
    except Exception as e:
        print(f"⚠️  Error handling cookie consent: {e}")
        return False

def search_google_for_profiles(page: Page, company_name: str) -> list[str]:
    """Searches Google for decision-maker profiles and returns a list of URLs."""
    print(f"Searching Google for decision-makers at '{company_name}'...")
    
    # More targeted search queries are better
    search_queries = [
        f'"{company_name}" CEO OR founder site:linkedin.com/in/',
        f'"{company_name}" executive site:twitter.com',
        f'"{company_name}" CTO site:linkedin.com/in/'
    ]
    
    profile_urls = set()
    
    for query in search_queries:
        print(f"  > Executing query: {query}")
        
        # Add random delay between queries
        human_like_delay()
        
        try:
            page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded")
            
            # Check for captcha and consent dialogs before proceeding
            if not handle_captcha_and_consent(page):
                print(f"❌ Failed to handle captcha/consent for query: {query}")
                continue
            
            # Debug: Let's see what's actually on the page
            print("🔍 Debugging page content...")
            try:
                page_title = page.title()
                print(f"    Page title: {page_title}")
                
                # Check if we're on a search results page
                if "google.com/search" in page.url:
                    print("    ✅ Confirmed: We're on Google search page")
                else:
                    print(f"    ⚠️  Unexpected URL: {page.url}")
                    
            except Exception as e:
                print(f"    ⚠️  Error getting page info: {e}")
                
        except Exception as e:
            print(f"❌ Error navigating to search page: {e}")
            print("🔄 Retrying with a new page...")
            try:
                # Create a new page if the current one is closed
                page = context.new_page()
                page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded")
                
                if not handle_captcha_and_consent(page):
                    print(f"❌ Failed to handle captcha/consent for query: {query}")
                    continue
            except Exception as retry_error:
                print(f"❌ Failed to retry: {retry_error}")
                continue
        
        # Look for search result links with multiple selectors
        try:
            # Wait for search results to load
            page.wait_for_timeout(3000)
            
            # Try multiple selectors for Google search results
            search_selectors = [
                'div.g a[href]',           # Standard Google results
                'div[data-hveid] a[href]', # Alternative Google format
                'div[jscontroller] a[href]', # Another Google format
                'h3 a[href]',              # Headline links
                'div[class*="g"] a[href]', # Generic Google result class
                'div[class*="result"] a[href]', # Result class
                'div[class*="search"] a[href]'  # Search class
            ]
            
            all_links = []
            for selector in search_selectors:
                try:
                    links = page.locator(selector).all()
                    if links:
                        all_links.extend(links)
                        print(f"    Found {len(links)} links with selector: {selector}")
                except:
                    continue
            
            # Remove duplicates and filter for profile URLs
            profile_links = []
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        # Debug: print what we're finding
                        if "linkedin.com/in/" in href or "twitter.com/" in href:
                            if "google.com" not in href:
                                profile_urls.add(href)
                                profile_links.append(href)
                                print(f"      ✅ Found profile: {href}")
                        elif "linkedin.com" in href or "twitter.com" in href:
                            print(f"      🔍 Found social link: {href}")
                        else:
                            print(f"      📄 Found other link: {href}")
                except Exception as e:
                    continue
            
            print(f"    Total links found: {len(all_links)}")
            print(f"    Profile URLs extracted: {len(profile_links)}")
            
        except Exception as e:
            print(f"    Error processing search results: {e}")
            continue
        
        # Add delay between queries to be respectful
        time.sleep(random.uniform(3, 6))
    
    print(f"Found {len(profile_urls)} potential profiles.")
    return list(profile_urls)

def create_browser_context(playwright, use_proxy=False, proxy_url=None):
    """Create a browser context with anti-detection measures"""
    
    # Browser launch options
    browser_options = {
        "headless": False,  # Keep visible for manual captcha solving
        "args": [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions-except",
            "--disable-plugins-discovery",
            "--disable-default-apps",
            "--no-first-run",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection"
        ]
    }
    
    browser = playwright.chromium.launch(**browser_options)
    
    # Context options
    context_options = {
        "no_viewport": True,
        "user_agent": random.choice(USER_AGENTS),
        "extra_http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    }
    
    # Add proxy if specified
    if use_proxy and proxy_url:
        context_options["proxy"] = {"server": proxy_url}
        print(f"🔒 Using proxy: {proxy_url}")
    
    context = browser.new_context(**context_options)
    
    # Add stealth scripts
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {},
        };
    """)
    
    return browser, context

# --- Main Functions ---

def load_cookies(context: BrowserContext, cookie_file_path: str):
    """Loads cookies from a file into the browser context."""
    if not os.path.exists(cookie_file_path):
        print(f"Warning: Cookie file not found at {cookie_file_path}. Proceeding without them.")
        return
    try:
        with open(cookie_file_path, 'r') as f:
            cookies = json.load(f)
        
        # Fix cookie format issues
        fixed_cookies = []
        for cookie in cookies:
            # Fix sameSite field if it's invalid
            if 'sameSite' in cookie:
                if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'  # Default to Lax
            
            # Ensure required fields exist
            if 'name' in cookie and 'value' in cookie and 'domain' in cookie:
                fixed_cookies.append(cookie)
            else:
                print(f"⚠️  Skipping invalid cookie: {cookie.get('name', 'unknown')}")
        
        if fixed_cookies:
            context.add_cookies(fixed_cookies)
            print(f"Successfully loaded {len(fixed_cookies)} cookies from {cookie_file_path}")
        else:
            print(f"⚠️  No valid cookies found in {cookie_file_path}")
            
    except Exception as e:
        print(f"Error loading cookies from {cookie_file_path}: {e}")
        print("Continuing without cookies...")

def scrape_linkedin_profile(page: Page, profile_url: str) -> dict:
    """Navigates to a LinkedIn profile and scrapes key information."""
    print(f"Scraping LinkedIn profile: {profile_url}")
    
    try:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for the main profile element to ensure the page is loaded
        page.wait_for_selector('h1', timeout=15000)

        # Scrape the data using specific selectors (these might need updating if LinkedIn changes its layout)
        name = page.locator('h1').first.inner_text().strip()
        headline = page.locator('div.text-body-medium.break-words').first.inner_text().strip()
        
        # Add more selectors for location, company, etc. if needed
        
        scraped_data = {
            "url": profile_url,
            "name": name,
            "headline": headline
        }
        
        return scraped_data
        
    except Exception as e:
        print(f"  -> Failed to scrape {profile_url}: {e}")
        return {"url": profile_url, "error": str(e)}

# --- Main Execution Block ---
if __name__ == "__main__":
    # The company you want to target
    target_company = "OpenAI" 

    all_leads_data = []

    with sync_playwright() as p:
        # Create browser with anti-detection measures
        browser, context = create_browser_context(p)
        
        # --- Step 1: Search on Google ---
        print("--- Phase 1: Google Search ---")
        google_page = context.new_page()
        load_cookies(context, GOOGLE_COOKIES_PATH)
        found_urls = search_google_for_profiles(google_page, target_company)
        google_page.close() # Close the page to save resources
        
        if not found_urls:
            print("No profiles found. Exiting.")
        else:
            # --- Step 2: Scrape Profiles ---
            print("\n--- Phase 2: Profile Scraping ---")
            # Create a new context for LinkedIn to load separate cookies if needed
            linkedin_context = browser.new_context()
            load_cookies(linkedin_context, LINKEDIN_COOKIES_PATH)
            
            linkedin_page = linkedin_context.new_page()
            
            for url in found_urls:
                if "linkedin.com" in url:
                    data = scrape_linkedin_profile(linkedin_page, url)
                    all_leads_data.append(data)
                    time.sleep(3) # Be respectful
                else:
                    print(f"Skipping non-LinkedIn URL for now: {url}")
            
            linkedin_page.close()
            linkedin_context.close()

        browser.close()

    # --- Step 3: Display Results ---
    print("\n--- Scraping Complete ---")
    print(json.dumps(all_leads_data, indent=2))

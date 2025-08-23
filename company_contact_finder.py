#!/usr/bin/env python3
"""
Company Contact Finder - Integrated Tool
=========================================

This tool combines CEO/executive search with company website scraping to find:
1. CEO emails and social media profiles (using Playwright + Google search)
2. Company contact information from their website (using Selenium)

Goal: For a given company domain (e.g., 'droplinked.com'), find:
- CEO/executive social handles and emails
- Company emails, phone numbers, and social media links
- Output everything in a structured JSON format

Author: Based on existing Contact_extractor.py and lead_finder.py
"""

import os
import re
import json
import time
import random
import traceback
import requests
from typing import Optional
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

# Selenium imports (for company website scraping)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup

# Playwright imports (for CEO search)
from playwright.sync_api import sync_playwright, Page, BrowserContext

# Load environment variables
load_dotenv()

# --- Configuration ---
# Selenium Chrome options for website scraping
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Get cookie paths from environment
GOOGLE_COOKIES_PATH = os.getenv("GOOGLE_COOKIES_PATH", "google-cookie.json")
LINKEDIN_COOKIES_PATH = os.getenv("LINKEDIN_COOKIES_PATH", "linkedin_cookies.json")

# --- Constants from original files ---
SOCIAL_MEDIA_DOMAINS = {
    'twitter.com': 'x',
    'x.com': 'x',
    'facebook.com': 'facebook',
    'fb.com': 'facebook',
    'instagram.com': 'instagram',
    'linkedin.com': 'linkedin',
    'youtube.com': 'youtube',
    'youtu.be': 'youtube',
    'pinterest.com': 'pinterest',
    'tiktok.com': 'tiktok',
    'snapchat.com': 'snapchat',
    'reddit.com': 'reddit',
    'tumblr.com': 'tumblr',
    'whatsapp.com': 'whatsapp',
    'wa.me': 'whatsapp',
    't.me': 'telegram',
    'telegram.me': 'telegram',
    'discord.gg': 'discord',
    'discord.com': 'discord',
    'medium.com': 'medium',
    'github.com': 'github',
    'threads.net': 'threads',
    'mastodon.social': 'mastodon'
}

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d{1,4}[-.\s()]?)?\(?\d{2,4}\)?[-.\s()]?\d{2,4}[-.\s()]?\d{2,5}"
MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 17

# User agents for human-like behavior
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

class CompanyContactFinder:
    def __init__(self):
        self.company_domain = None
        self.company_name = None
        self.results = {
            "company_domain": None,
            "company_name": None,
            "company_website_data": {},
            "ceo_data": {},
            "timestamp": int(time.time()),
            "success": False,
            "errors": []
        }
        
        # Create output directory for JSON reports
        self.output_dir = "contact_finder_reports"
        self.ensure_output_directory()

    def human_like_delay(self, min_delay=2, max_delay=5):
        """Add random delays to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def normalize_url(self, url):
        """Normalize URL to get the landing page URL with retry mechanism"""
        if not url:
            return None, None
            
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            # Parse the URL to get the base domain
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Try multiple times with different timeouts
            for attempt in range(3):
                try:
                    timeout = 5 + (attempt * 5)  # 5, 10, 15 seconds
                    print(f"🔄 Attempting to connect to {base_url} (attempt {attempt + 1}, timeout: {timeout}s)")
                    
                    # Make a HEAD request to check for redirects
                    response = requests.head(base_url, allow_redirects=True, timeout=timeout)
                    final_url = response.url
                    
                    # Parse the final URL to get the base domain
                    parsed = urlparse(final_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"

                    display_url = parsed.netloc
                    if display_url.startswith("www."):
                        display_url = display_url[4:]
                    
                    print(f"✅ Successfully connected to {base_url}")
                    return base_url, display_url
                    
                except requests.exceptions.Timeout:
                    print(f"⏰ Timeout on attempt {attempt + 1}")
                    if attempt == 2:  # Last attempt
                        print(f"🔄 Using direct URL without redirect check: {base_url}")
                        # Return the original URL without redirect check
                        parsed = urlparse(base_url)
                        display_url = parsed.netloc
                        if display_url.startswith("www."):
                            display_url = display_url[4:]
                        return base_url, display_url
                except Exception as e:
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    if attempt == 2:  # Last attempt, return basic URL
                        parsed = urlparse(base_url)
                        display_url = parsed.netloc
                        if display_url.startswith("www."):
                            display_url = display_url[4:]
                        return base_url, display_url
                    
        except Exception as e:
            print(f"Error normalizing URL {url}: {e}")
            return None, None

    def extract_company_name_from_domain(self, domain):
        """Extract company name from domain for search queries"""
        # Remove common TLDs and www
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Split by dot and take the main part
        domain_parts = domain.split('.')
        if len(domain_parts) > 0:
            company_name = domain_parts[0]
            # Convert to title case for better search results
            return company_name.replace('-', ' ').replace('_', ' ').title()
        return domain

    def categorize_social_link(self, url):
        """Categorize social media links"""
        try:
            if not url or not isinstance(url, str):
                return None, url
            if not url.startswith(('http://', 'https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                else:
                    url = 'https://' + url
            url_obj = urlparse(url)
            hostname = url_obj.netloc.lower().replace('www.', '')
            if not hostname:
                return None, url
            for domain, category in SOCIAL_MEDIA_DOMAINS.items():
                if hostname == domain or hostname.endswith('.' + domain):
                    return category, url
            return None, url
        except Exception:
            return None, url

    def is_plausible_phone_candidate(self, candidate_str, min_digits=MIN_PHONE_DIGITS, max_digits=MAX_PHONE_DIGITS):
        """Validate if a string is a plausible phone number"""
        candidate_str = candidate_str.strip()
        if not candidate_str or len(candidate_str) < min_digits - 4:
            return False

        # Basic validation - check digit count
        digits_only = "".join(filter(str.isdigit, candidate_str))
        num_digits = len(digits_only)
        
        if not (min_digits <= num_digits <= max_digits):
            return False

        # Reject all same digits
        if len(set(digits_only)) == 1 and num_digits >= 7:
            return False
        
        return True

    def handle_captcha_and_consent(self, page: Page) -> bool:
        """Handle Google captcha challenges and cookie consent dialogs"""
        print("🔍 Checking for captcha or consent dialogs...")
        
        # First, try to handle cookie consent dialogs
        try:
            page.wait_for_timeout(2000)
            
            # Common cookie consent button selectors
            consent_selectors = [
                "button[aria-label*='Accept all']",
                "button:has-text('Accept all')",
                "button:has-text('Accept')",
                "button[data-identifier*='accept']",
                "button[id*='accept']"
            ]
            
            for selector in consent_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        print(f"🎯 Found consent button: {selector}")
                        page.locator(selector).first.click()
                        print("✅ Clicked consent button!")
                        page.wait_for_timeout(2000)
                        break
                except:
                    continue
        except:
            pass
        
        # Check for captchas
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
        
        if captcha_found:
            print("🔒 Captcha challenge detected!")
            print("🔄 Waiting for manual captcha solution...")
            print("Please solve the captcha manually in the browser window.")
            
            try:
                # Wait for captcha to be solved (look for search results)
                page.wait_for_selector('div.g', timeout=120000)  # 2 minutes timeout
                print("✅ Captcha appears to be solved! Continuing...")
                return True
            except:
                print("⏰ Timeout waiting for captcha solution.")
                return False
        
        return True

    def search_ceo_profiles(self, company_name: str, page: Page) -> list:
        """Search Google for CEO profiles only - first result validation approach"""
        print(f"🔍 Searching for CEO of '{company_name}' (first result only approach)...")
        
        # Focused search queries - ONLY CEO, one per platform
        search_queries = [
            f'"{company_name}" CEO site:twitter.com',
            f'"{company_name}" CEO site:x.com', 
            f'"{company_name}" CEO site:linkedin.com/in/',
            f'"{company_name}" CEO site:instagram.com',
            f'"{company_name}" CEO site:tiktok.com'
        ]
        
        ceo_profiles = []
        
        for query in search_queries:
            print(f"  📝 Query: {query}")
            self.human_like_delay(3, 5)  # Longer delay for precision
            
            try:
                # Navigate to Google search
                page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded")
                
                # Handle captcha and consent
                if not self.handle_captcha_and_consent(page):
                    print(f"❌ Failed to handle captcha/consent for query: {query}")
                    continue
                
                # Wait for search results
                page.wait_for_timeout(4000)
                
                # Get ONLY the first search result
                first_result_url = self.get_first_search_result(page, query)
                
                if first_result_url and self.is_valid_ceo_profile_url(first_result_url):
                    platform = self.get_platform_from_url(first_result_url)
                    print(f"      ✅ Found CEO on {platform}: {first_result_url}")
                    ceo_profiles.append(first_result_url)
                else:
                    platform = self.get_platform_from_query(query)
                    print(f"      ❌ No valid CEO profile found on {platform} (first result not valid)")
                    
            except Exception as e:
                print(f"❌ Error searching for query '{query}': {e}")
                continue
        
        print(f"🎯 Found {len(ceo_profiles)} CEO profiles (first result validation)")
        return ceo_profiles
    
    def get_first_search_result(self, page: Page, query: str) -> Optional[str]:
        """Get the first search result URL from Google with improved extraction"""
        try:
            # Wait a bit longer for search results to fully load
            page.wait_for_timeout(5000)
            
            # Try multiple approaches to get the first actual result
            approaches = [
                # Approach 1: Standard Google result selectors
                {
                    'name': 'Standard Google Results',
                    'selectors': [
                        'div.g:first-of-type h3 a[href]',  # First result title link
                        'div.g:first-of-type a[href]:not([href*="google.com"])',  # First result any link (not Google)
                        'div.tF2Cxc:first-of-type h3 a[href]',  # Alternative Google format
                        'div[data-hveid]:first-of-type h3 a[href]'  # Data-hveid format
                    ]
                },
                # Approach 2: Generic result containers
                {
                    'name': 'Generic Results',
                    'selectors': [
                        '#search div.g a[href]:not([href*="google.com"]):not([href*="/search"])',
                        '#rso div.g a[href]:not([href*="google.com"]):not([href*="/search"])',
                        'div[data-hveid] a[href]:not([href*="google.com"]):not([href*="/search"])'
                    ]
                },
                # Approach 3: Direct link extraction
                {
                    'name': 'Direct Links',
                    'selectors': [
                        'a[href*="linkedin.com/in/"]:first',
                        'a[href*="twitter.com/"]:first',
                        'a[href*="x.com/"]:first',
                        'a[href*="instagram.com/"]:first',
                        'a[href*="tiktok.com/"]:first'
                    ]
                }
            ]
            
            print(f"      🔍 Extracting first result for: {query}")
            
            for approach in approaches:
                print(f"        Trying {approach['name']}...")
                
                for selector in approach['selectors']:
                    try:
                        elements = page.locator(selector).all()
                        print(f"          Selector '{selector}': Found {len(elements)} elements")
                        
                        for i, element in enumerate(elements[:3]):  # Check first 3 elements
                            try:
                                href = element.get_attribute('href')
                                if href:
                                    # Make URL absolute if needed
                                    if href.startswith('/'):
                                        href = 'https://google.com' + href
                                    elif not href.startswith(('http://', 'https://')):
                                        href = 'https://' + href
                                    
                                    print(f"            [{i+1}] Found URL: {href}")
                                    
                                    # Skip Google internal URLs
                                    if any(skip in href for skip in ['google.com', '/search?', '/url?']):
                                        print(f"            [{i+1}] Skipped (Google internal)")
                                        continue
                                    
                                    # This looks like a real external URL
                                    print(f"            [{i+1}] ✅ Valid external URL found!")
                                    return href
                                    
                            except Exception as e:
                                print(f"            [{i+1}] Error getting href: {e}")
                                continue
                                
                    except Exception as e:
                        print(f"          Selector '{selector}' failed: {e}")
                        continue
            
            # If no direct links found, try getting all links and find the first relevant one
            print(f"        Fallback: Extracting all links...")
            try:
                all_links = page.locator('a[href]').all()
                print(f"          Found {len(all_links)} total links")
                
                target_domains = ['linkedin.com', 'twitter.com', 'x.com', 'instagram.com', 'tiktok.com']
                
                for i, link in enumerate(all_links[:20]):  # Check first 20 links
                    try:
                        href = link.get_attribute('href')
                        if href and any(domain in href for domain in target_domains):
                            # Skip Google redirects
                            if '/url?' in href or 'google.com' in href:
                                continue
                                
                            print(f"          [{i+1}] Found target domain link: {href}")
                            return href
                            
                    except:
                        continue
                        
            except Exception as e:
                print(f"        Fallback extraction failed: {e}")
            
            print(f"      ❌ No valid first result found for: {query}")
            return None
            
        except Exception as e:
            print(f"      ❌ Error in get_first_search_result: {e}")
            return None
    
    def is_valid_ceo_profile_url(self, url: str) -> bool:
        """Validate if URL is a proper social media profile with correct handle format"""
        if not url:
            return False
            
        # Handle Google redirect URLs
        if '/url?' in url and 'google.com' in url:
            try:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(url)
                if parsed.query:
                    query_params = parse_qs(parsed.query)
                    if 'url' in query_params:
                        actual_url = query_params['url'][0]
                        print(f"      🔄 Extracted from Google redirect: {actual_url}")
                        url = actual_url
                    elif 'q' in query_params:
                        actual_url = query_params['q'][0]
                        print(f"      🔄 Extracted from Google redirect: {actual_url}")
                        url = actual_url
            except Exception as e:
                print(f"      ❌ Error extracting from redirect: {e}")
                return False
        
        # Skip obvious Google URLs
        if "google.com" in url or "/search?" in url:
            print(f"      ❌ Google internal URL: {url}")
            return False
        
        # Must be a full URL starting with http/https
        if not url.startswith(('http://', 'https://')):
            print(f"      ❌ Not a full URL: {url}")
            return False
        
        # Parse URL for detailed validation
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # Remove www. for domain checking
            if domain.startswith('www.'):
                domain = domain[4:]
            
            print(f"      🔍 Validating: domain='{domain}', path='{path}'")
            
            # Platform-specific validation with EXACT format requirements
            
            # 1. LinkedIn: Must be linkedin.com/in/username format
            if 'linkedin.com' in domain:
                if not path.startswith('/in/'):
                    print(f"      ❌ LinkedIn URL must have /in/ path, got: {path}")
                    return False
                if path.count('/') != 2:  # Should be /in/username only
                    print(f"      ❌ LinkedIn URL has too many path segments: {path}")
                    return False
                username = path.replace('/in/', '')
                if not username or len(username) < 2:
                    print(f"      ❌ LinkedIn username too short: '{username}'")
                    return False
                print(f"      ✅ Valid LinkedIn profile format: /in/{username}")
                return True
            
            # 2. X/Twitter: Must be x.com/username or twitter.com/username format (NO extra paths)
            elif domain in ['x.com', 'twitter.com']:
                # Must be exactly /username format (one path segment only)
                if path.count('/') != 1 or not path.startswith('/'):
                    print(f"      ❌ X/Twitter URL must be /username format, got: {path}")
                    return False
                
                username = path[1:]  # Remove leading /
                if not username or len(username) < 2:
                    print(f"      ❌ X/Twitter username too short: '{username}'")
                    return False
                
                # Check for invalid paths that indicate non-profile pages
                invalid_paths = ['highlights', 'status', 'search', 'i', 'home', 'notifications', 'messages']
                if username.lower() in invalid_paths:
                    print(f"      ❌ X/Twitter URL is not a profile (invalid path): {username}")
                    return False
                    
                print(f"      ✅ Valid X/Twitter profile format: /{username}")
                return True
            
            # 3. Instagram: Must be instagram.com/username format (NO /p/, /reel/, etc.)
            elif 'instagram.com' in domain:
                # Must be exactly /username format (one path segment only)
                if path.count('/') != 1 or not path.startswith('/'):
                    print(f"      ❌ Instagram URL must be /username format, got: {path}")
                    return False
                
                username = path[1:]  # Remove leading /
                if not username or len(username) < 2:
                    print(f"      ❌ Instagram username too short: '{username}'")
                    return False
                
                # Check for invalid paths that indicate posts/reels
                if username in ['p', 'reel', 'tv', 'explore', 'stories']:
                    print(f"      ❌ Instagram URL is not a profile (invalid path): {username}")
                    return False
                    
                print(f"      ✅ Valid Instagram profile format: /{username}")
                return True
            
            # 4. TikTok: Must be tiktok.com/@username format (MUST have @ symbol)
            elif 'tiktok.com' in domain:
                # Must be exactly /@username format
                if not path.startswith('/@'):
                    print(f"      ❌ TikTok URL must be /@username format, got: {path}")
                    return False
                
                if path.count('/') != 1:  # Should be /@username only
                    print(f"      ❌ TikTok URL has too many path segments: {path}")
                    return False
                
                username = path[2:]  # Remove /@
                if not username or len(username) < 2:
                    print(f"      ❌ TikTok username too short: '{username}'")
                    return False
                
                # Check for invalid paths that indicate discover/video pages
                if username.lower() in ['discover', 'video', 'search', 'trending', 'following']:
                    print(f"      ❌ TikTok URL is not a profile (invalid path): @{username}")
                    return False
                    
                print(f"      ✅ Valid TikTok profile format: /@{username}")
                return True
            
            else:
                print(f"      ❌ Unsupported social media platform: {domain}")
                return False
                
        except Exception as e:
            print(f"      ❌ Error parsing URL: {e}")
            return False
    
    def get_platform_from_url(self, url: str) -> str:
        """Extract platform name from URL"""
        if "twitter.com" in url or "x.com" in url:
            return "Twitter/X"
        elif "linkedin.com" in url:
            return "LinkedIn"
        elif "instagram.com" in url:
            return "Instagram"
        elif "tiktok.com" in url:
            return "TikTok"
        return "Unknown"
    
    def get_platform_from_query(self, query: str) -> str:
        """Extract platform name from search query"""
        if "twitter.com" in query or "x.com" in query:
            return "Twitter/X"
        elif "linkedin.com" in query:
            return "LinkedIn"
        elif "instagram.com" in query:
            return "Instagram"
        elif "tiktok.com" in query:
            return "TikTok"
        return "Unknown"

    def ensure_output_directory(self):
        """Create output directory for JSON reports if it doesn't exist"""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"📁 Created output directory: {self.output_dir}")
        except Exception as e:
            print(f"⚠️ Could not create output directory: {e}")
            # Fallback to current directory
            self.output_dir = "."

    def get_organized_filename(self):
        """Generate organized filename with company name and timestamp"""
        timestamp = int(time.time())
        
        # Clean company domain for filename
        clean_domain = self.company_domain.replace('.', '_').replace('/', '').replace(':', '') if self.company_domain else 'unknown'
        
        # Create date-based subdirectory
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(self.output_dir, date_str)
        
        try:
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
                print(f"📅 Created date directory: {date_dir}")
        except Exception as e:
            print(f"⚠️ Could not create date directory, using main output dir: {e}")
            date_dir = self.output_dir
        
        filename = f"company_contacts_{clean_domain}_{timestamp}.json"
        return os.path.join(date_dir, filename)

    def scrape_profile_info(self, profile_url: str, page: Page) -> dict:
        """Scrape CEO information from social profile"""
        platform = self.get_platform_from_url(profile_url)
        print(f"👤 Scraping CEO profile on {platform}: {profile_url}")
        
        try:
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            
            profile_data = {
                "url": profile_url,
                "platform": platform.lower().replace("/", "_"),
                "name": "",
                "headline": "",
                "error": None
            }
            
            # Platform-specific scraping
            if "twitter.com" in profile_url or "x.com" in profile_url:
                # Twitter/X scraping
                try:
                    # Try to get name
                    name_selectors = [
                        '[data-testid="UserName"] span',
                        '.css-901oao.r-1awozwy.r-6koalj.r-37j5jr.r-a023e6.r-16dba41.r-rjixqe.r-bcqeeo.r-qvutc0'
                    ]
                    for selector in name_selectors:
                        try:
                            name_element = page.locator(selector).first
                            if name_element.count() > 0:
                                profile_data["name"] = name_element.inner_text().strip()
                                break
                        except:
                            continue
                    
                    # Try to get bio/headline
                    bio_selectors = [
                        '[data-testid="UserDescription"]',
                        '.css-901oao.r-18jsvk2.r-37j5jr.r-a023e6.r-16dba41.r-rjixqe.r-bcqeeo.r-bnwqim.r-qvutc0'
                    ]
                    for selector in bio_selectors:
                        try:
                            bio_element = page.locator(selector).first
                            if bio_element.count() > 0:
                                profile_data["headline"] = bio_element.inner_text().strip()
                                break
                        except:
                            continue
                            
                except Exception as e:
                    profile_data["error"] = f"Twitter scraping error: {e}"
            
            elif "linkedin.com" in profile_url:
                # LinkedIn scraping (more comprehensive attempt)
                try:
                    print(f"            Attempting LinkedIn scraping for: {profile_url}")
                    
                    # LinkedIn name - try multiple selectors
                    name_selectors = [
                        'h1.text-heading-xlarge',
                        '.pv-text-details__left-panel h1',
                        'h1[data-generated-suggestion-target]',
                        '.pv-top-card--list h1',
                        'h1.pv-top-card-section__name',
                        '.profile-hero__name h1',
                        'h1',  # Fallback to any h1
                    ]
                    
                    for i, selector in enumerate(name_selectors):
                        try:
                            print(f"              Trying name selector {i+1}: {selector}")
                            name_elements = page.locator(selector).all()
                            print(f"              Found {len(name_elements)} elements")
                            
                            for j, name_element in enumerate(name_elements[:3]):
                                try:
                                    name_text = name_element.inner_text().strip()
                                    print(f"              Element {j+1} text: '{name_text}'")
                                    
                                    if name_text and len(name_text) > 2 and len(name_text) < 100:
                                        profile_data["name"] = name_text
                                        print(f"              ✅ Found name: {name_text}")
                                        break
                                except Exception as e:
                                    print(f"              Error extracting text from element {j+1}: {e}")
                                    continue
                                    
                            if profile_data["name"]:
                                break
                                
                        except Exception as e:
                            print(f"              Selector {i+1} failed: {e}")
                            continue
                    
                    # LinkedIn headline - try multiple selectors
                    headline_selectors = [
                        '.text-body-medium.break-words',
                        '.pv-text-details__left-panel .text-body-medium',
                        '[data-generated-suggestion-target] + div',
                        '.pv-top-card--list-bullet .pv-entity__summary-info h2',
                        '.pv-top-card-section__headline',
                        '.profile-hero__subtitle',
                        'div.text-body-medium'
                    ]
                    
                    for i, selector in enumerate(headline_selectors):
                        try:
                            print(f"              Trying headline selector {i+1}: {selector}")
                            headline_elements = page.locator(selector).all()
                            print(f"              Found {len(headline_elements)} elements")
                            
                            for j, headline_element in enumerate(headline_elements[:3]):
                                try:
                                    headline_text = headline_element.inner_text().strip()
                                    print(f"              Element {j+1} text: '{headline_text}'")
                                    
                                    if headline_text and len(headline_text) > 5 and len(headline_text) < 200:
                                        profile_data["headline"] = headline_text
                                        print(f"              ✅ Found headline: {headline_text}")
                                        break
                                except Exception as e:
                                    print(f"              Error extracting headline from element {j+1}: {e}")
                                    continue
                                    
                            if profile_data["headline"]:
                                break
                                
                        except Exception as e:
                            print(f"              Headline selector {i+1} failed: {e}")
                            continue
                            
                    # If still no data, try to get page title or any text
                    if not profile_data["name"] and not profile_data["headline"]:
                        try:
                            page_title = page.title()
                            print(f"              Page title: {page_title}")
                            
                            if "LinkedIn" in page_title and "|" in page_title:
                                # LinkedIn titles often have format "Name | Headline | LinkedIn"
                                parts = page_title.split("|", 2)
                                if len(parts) >= 2:
                                    potential_name = parts[0].strip()
                                    potential_headline = parts[1].strip()
                                    
                                    if potential_name and len(potential_name) > 2:
                                        profile_data["name"] = potential_name
                                        print(f"              ✅ Found name from title: {potential_name}")
                                    
                                    if potential_headline and len(potential_headline) > 2:
                                        profile_data["headline"] = potential_headline
                                        print(f"              ✅ Found headline from title: {potential_headline}")
                                        
                        except Exception as e:
                            print(f"              Error extracting from page title: {e}")
                            
                except Exception as e:
                    profile_data["error"] = f"LinkedIn scraping error: {e}"
                    print(f"            LinkedIn scraping failed: {e}")
            
            elif "instagram.com" in profile_url:
                # Instagram scraping
                try:
                    # Instagram name/username
                    name_selectors = [
                        'h2._aacl._aaco._aacu._aacx._aad7._aade',
                        'h1._aacl._aaco._aacu._aacx._aad6._aade'
                    ]
                    for selector in name_selectors:
                        try:
                            name_element = page.locator(selector).first
                            if name_element.count() > 0:
                                profile_data["name"] = name_element.inner_text().strip()
                                break
                        except:
                            continue
                    
                    # Instagram bio
                    bio_selectors = [
                        '._aa_c span',
                        'div.-vDIg span'
                    ]
                    for selector in bio_selectors:
                        try:
                            bio_element = page.locator(selector).first
                            if bio_element.count() > 0:
                                profile_data["headline"] = bio_element.inner_text().strip()
                                break
                        except:
                            continue
                            
                except Exception as e:
                    profile_data["error"] = f"Instagram scraping error: {e}"
            
            elif "tiktok.com" in profile_url:
                # TikTok scraping
                try:
                    # TikTok username/name
                    name_selectors = [
                        '[data-e2e="user-title"]',
                        'h2[data-e2e="user-title"]'
                    ]
                    for selector in name_selectors:
                        try:
                            name_element = page.locator(selector).first
                            if name_element.count() > 0:
                                profile_data["name"] = name_element.inner_text().strip()
                                break
                        except:
                            continue
                    
                    # TikTok bio
                    bio_selectors = [
                        '[data-e2e="user-bio"]',
                        'h2[data-e2e="user-bio"]'
                    ]
                    for selector in bio_selectors:
                        try:
                            bio_element = page.locator(selector).first
                            if bio_element.count() > 0:
                                profile_data["headline"] = bio_element.inner_text().strip()
                                break
                        except:
                            continue
                            
                except Exception as e:
                    profile_data["error"] = f"TikTok scraping error: {e}"
            
            # Log the result
            if profile_data["name"]:
                print(f"      ✅ CEO found: {profile_data['name']} on {platform}")
            else:
                print(f"      ⚠️  Profile found but no name extracted on {platform}")
            
            return profile_data
            
        except Exception as e:
            return {
                "url": profile_url,
                "platform": platform.lower().replace("/", "_"),
                "name": "",
                "headline": "",
                "error": str(e)
            }

    def scrape_company_website(self, company_url: str) -> dict:
        """Scrape company website for contact information using Selenium"""
        print(f"🌐 Scraping company website: {company_url}")
        
        driver = None
        try:
            # Setup Selenium driver with better error handling
            try:
                driver_path = os.environ.get("DRIVER_PATH")
                if driver_path and os.path.exists(driver_path):
                    service = Service(executable_path=driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    # Try to use ChromeDriverManager or system Chrome
                    try:
                        # First try without specifying service
                        driver = webdriver.Chrome(options=chrome_options)
                    except Exception as e1:
                        print(f"⚠️  Chrome driver not found, trying alternative methods...")
                        # Try with webdriver-manager if available
                        try:
                            from webdriver_manager.chrome import ChromeDriverManager
                            service = Service(ChromeDriverManager().install())
                            driver = webdriver.Chrome(service=service, options=chrome_options)
                            print("✅ Using webdriver-manager for Chrome driver")
                        except ImportError:
                            print("💡 Tip: Install webdriver-manager with: pip install webdriver-manager")
                            raise e1
            except Exception as driver_error:
                return {
                    "domain": company_url,
                    "error": f"Chrome driver setup failed: {driver_error}. Please install Chrome and/or webdriver-manager.",
                    "success": False
                }
            
            driver.set_page_load_timeout(30)
            driver.delete_all_cookies()
            
            driver.get(company_url)
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except TimeoutException:
                print(f"⚠️ Body not found quickly, proceeding...")
            
            page_source = driver.page_source
            if not page_source:
                return {"error": "Empty page source"}
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Initialize collections
            social_links = {}
            emails_found = set()
            phones_found = set()
            
            # Extract all links for emails and social media
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if not href or not isinstance(href, str):
                    continue
                href = href.strip()
                if not href:
                    continue
                
                # Extract emails from mailto links
                if href.startswith('mailto:'):
                    try:
                        email_part = unquote(href.split('mailto:', 1)[1].split('?')[0]).strip()
                        if re.fullmatch(EMAIL_REGEX, email_part):
                            emails_found.add(email_part)
                    except:
                        pass
                    continue
                
                # Extract phones from tel links
                if href.startswith('tel:'):
                    try:
                        phone_part = href.split('tel:', 1)[1].strip()
                        if self.is_plausible_phone_candidate(phone_part, min_digits=6, max_digits=20):
                            phones_found.add(phone_part)
                    except:
                        pass
                
                # Extract social media links
                try:
                    abs_href = href
                    parsed_original_url = urlparse(company_url)
                    if not abs_href.startswith(('http://', 'https://')):
                        if abs_href.startswith('//'):
                            abs_href = (parsed_original_url.scheme or 'https') + ':' + abs_href
                        elif abs_href.startswith('/'):
                            base_url = f"{(parsed_original_url.scheme or 'https')}://{parsed_original_url.netloc}"
                            abs_href = f"{base_url}{abs_href}"
                        else:
                            abs_href = (parsed_original_url.scheme or 'https') + '://' + abs_href
                    
                    social_type, social_url = self.categorize_social_link(abs_href)
                    if social_type and social_type not in social_links:
                        social_links[social_type] = social_url
                except:
                    pass
            
            # Extract emails from page text
            if soup.body:
                try:
                    body_text = soup.body.get_text(separator=' ', strip=True)
                    emails_found.update(re.findall(EMAIL_REGEX, body_text))
                except:
                    pass
            
            # Extract phone numbers from footer
            footer_elements = soup.find_all('footer')
            if not footer_elements:
                footer_elements = soup.select('.footer, #footer, [class*="site-footer"], [id*="site-footer"], [role="contentinfo"]')
            
            if footer_elements:
                for footer_el in footer_elements:
                    footer_text = footer_el.get_text(separator=' ', strip=True)
                    try:
                        candidate_phones = set()
                        for match in re.finditer(PHONE_REGEX, footer_text):
                            candidate_phones.add(match.group(0).strip())
                        
                        for phone_candidate in candidate_phones:
                            if self.is_plausible_phone_candidate(phone_candidate):
                                phones_found.add(phone_candidate)
                    except Exception as e:
                        print(f"Error extracting phones from footer: {e}")
            
            # Extract logo URL
            logo_url = None
            try:
                # Look for common logo selectors
                logo_selectors = ['img[alt*="logo" i]', 'img[class*="logo" i]', 'img[id*="logo" i]']
                for selector in logo_selectors:
                    logo_img = soup.select_one(selector)
                    if logo_img and logo_img.get('src'):
                        src_value = logo_img.get('src')
                        # Handle case where src might be a list
                        if isinstance(src_value, list) and src_value:
                            logo_url = str(src_value[0])
                        elif isinstance(src_value, str):
                            logo_url = src_value
                        else:
                            continue
                        
                        # Make absolute URL if needed
                        if not logo_url.startswith(('http://', 'https://')):
                            parsed_url = urlparse(company_url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            if logo_url.startswith('/'):
                                logo_url = base_url + logo_url
                        break
            except Exception as e:
                print(f"Error extracting logo: {e}")
            
            return {
                "domain": company_url,
                "logo_url": logo_url,
                "emails": sorted(list(emails_found)),
                "phones": sorted(list(phones_found)),
                "social_links": social_links,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Error scraping company website: {e}")
            
            # Fallback: try using the existing Contact_extractor scraping method
            print("🔄 Trying fallback method using existing Contact_extractor logic...")
            try:
                from Contact_extractor import scrape_domain
                result, status_code = scrape_domain(company_url.replace('https://', '').replace('http://', ''))
                if status_code == 200 and "error" not in result:
                    return {
                        "domain": company_url,
                        "logo_url": result.get("logoURL"),
                        "emails": result.get("emails", []),
                        "phones": result.get("phones", []),
                        "social_links": result.get("socialLinks", {}),
                        "success": True,
                        "method": "fallback_contact_extractor"
                    }
                else:
                    return {
                        "domain": company_url,
                        "error": f"Both methods failed. Primary: {e}. Fallback: {result.get('error', 'Unknown error')}",
                        "success": False
                    }
            except Exception as fallback_error:
                return {
                    "domain": company_url,
                    "error": f"Both methods failed. Primary: {e}. Fallback: {fallback_error}",
                    "success": False
                }
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def find_company_contacts(self, company_domain: str) -> dict:
        """Main method to find all company contacts - CEO profiles + website data"""
        print(f"\n🚀 Starting Company Contact Finder for: {company_domain}")
        print("=" * 60)
        
        self.company_domain = company_domain
        self.results["company_domain"] = company_domain
        
        # Normalize the company URL
        company_url, display_domain = self.normalize_url(company_domain)
        if not company_url:
            self.results["errors"].append("Invalid or unreachable company URL")
            return self.results
        
        # Extract company name for search
        self.company_name = self.extract_company_name_from_domain(display_domain)
        self.results["company_name"] = self.company_name
        
        print(f"📊 Company: {self.company_name}")
        print(f"🌐 Website: {company_url}")
        
        # Step 1: Search for CEO/Executive profiles using Playwright
        print(f"\n🔍 STEP 1: Searching for CEO/Executive profiles...")
        ceo_profiles = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with enhanced stealth settings
                browser = p.chromium.launch(
                    headless=False,  # Set to True for headless mode
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-plugins',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-default-apps',
                        '--disable-popup-blocking',
                        '--disable-translate',
                        '--disable-background-timer-throttling',
                        '--disable-renderer-backgrounding',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-client-side-phishing-detection',
                        '--disable-sync',
                        '--metrics-recording-only',
                        '--no-report-upload',
                        '--disable-background-networking',
                        '--enable-features=NetworkService,NetworkServiceLogging',
                        '--force-color-profile=srgb',
                        '--disable-features=TranslateUI'
                    ]
                )
                
                # Create context with random user agent and extra headers
                context = browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                # Load Google cookies if available
                if os.path.exists(GOOGLE_COOKIES_PATH):
                    try:
                        with open(GOOGLE_COOKIES_PATH, 'r') as f:
                            raw_cookies = json.load(f)
                        
                        # Convert cookies to Playwright format
                        playwright_cookies = []
                        for cookie in raw_cookies:
                            # Convert sameSite field to proper format
                            same_site = cookie.get('sameSite')
                            if same_site is None:
                                same_site = 'None'
                            elif same_site == 'no_restriction':
                                same_site = 'None'
                            elif same_site == 'lax':
                                same_site = 'Lax'
                            elif same_site == 'strict':
                                same_site = 'Strict'
                            
                            playwright_cookie = {
                                'name': cookie['name'],
                                'value': cookie['value'],
                                'domain': cookie['domain'],
                                'path': cookie['path'],
                                'httpOnly': cookie.get('httpOnly', False),
                                'secure': cookie.get('secure', False),
                                'sameSite': same_site
                            }
                            
                            # Add expiration if present and not a session cookie
                            if not cookie.get('session', False) and 'expirationDate' in cookie:
                                playwright_cookie['expires'] = int(cookie['expirationDate'])
                            
                            playwright_cookies.append(playwright_cookie)
                        
                        context.add_cookies(playwright_cookies)
                        print(f"✅ Google cookies loaded successfully ({len(playwright_cookies)} cookies)")
                    except Exception as e:
                        print(f"⚠️ Could not load Google cookies: {e}")
                        print("🔄 Continuing without cookies...")
                
                page = context.new_page()
                
                # Add extra stealth measures
                page.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """)
                
                # Search for CEO profiles
                profile_urls = self.search_ceo_profiles(self.company_name, page)
                
                # Scrape each CEO profile for detailed information
                ceo_profiles_data = []
                for profile_url in profile_urls:
                    self.human_like_delay(2, 4)  # Respectful delay between profile scraping
                    profile_data = self.scrape_profile_info(profile_url, page)
                    ceo_profiles_data.append(profile_data)
                
                browser.close()
                
        except Exception as e:
            error_msg = f"Error in CEO profile search: {e}"
            print(f"❌ {error_msg}")
            self.results["errors"].append(error_msg)
            ceo_profiles_data = []
        
        # Organize CEO data by platform
        ceo_data = {
            "search_method": "first_result_validation",
            "platforms_searched": ["Twitter/X", "LinkedIn", "Instagram", "TikTok"],
            "profiles_found": len(ceo_profiles_data),
            "ceo_profiles": {}
        }
        
        # Group by platform for cleaner presentation
        for profile in ceo_profiles_data:
            platform = profile.get("platform", "unknown")
            ceo_data["ceo_profiles"][platform] = {
                "url": profile.get("url"),
                "name": profile.get("name"),
                "headline": profile.get("headline"),
                "found": bool(profile.get("name")),
                "error": profile.get("error")
            }
        
        self.results["ceo_data"] = ceo_data
        
        # Count successful CEO finds
        successful_ceo_finds = sum(1 for p in ceo_profiles_data if p.get("name"))
        print(f"✅ CEO search complete: {successful_ceo_finds} successful profile(s) found")
        
        # Step 2: Scrape company website for contact information
        print(f"\n🌐 STEP 2: Scraping company website for contacts...")
        
        website_data = self.scrape_company_website(company_url)
        self.results["company_website_data"] = website_data
        
        if website_data.get("success"):
            emails_count = len(website_data.get("emails", []))
            phones_count = len(website_data.get("phones", []))
            socials_count = len(website_data.get("social_links", {}))
            print(f"✅ Website scraping complete: {emails_count} emails, {phones_count} phones, {socials_count} social links")
        else:
            print(f"❌ Website scraping failed: {website_data.get('error', 'Unknown error')}")
        
        # Mark as successful if we got some data
        if (successful_ceo_finds > 0 or website_data.get("success")):
            self.results["success"] = True
        
        print(f"\n📋 SUMMARY:")
        print(f"   🏢 Company: {self.company_name}")
        print(f"   👤 CEO Profiles Found: {successful_ceo_finds} (first result validation)")
        
        # Show which platforms found the CEO
        for platform, data in ceo_data.get("ceo_profiles", {}).items():
            status = "✅" if data.get("found") else "❌"
            name = f" - {data.get('name')}" if data.get("name") else ""
            print(f"     {status} {platform.title()}{name}")
        
        print(f"   📧 Company Emails: {len(website_data.get('emails', []))}")
        print(f"   📞 Company Phones: {len(website_data.get('phones', []))}")
        print(f"   🔗 Social Links: {len(website_data.get('social_links', {}))}")
        print("=" * 60)
        
        return self.results

    def save_results_to_json(self, filename=None):
        """Save results to organized JSON file"""
        if not filename:
            filename = self.get_organized_filename()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            # Fallback to simple filename in current directory
            try:
                timestamp = int(time.time())
                fallback_filename = f"company_contacts_backup_{timestamp}.json"
                with open(fallback_filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False)
                print(f"💾 Fallback: Results saved to: {fallback_filename}")
                return fallback_filename
            except Exception as fallback_error:
                print(f"❌ Fallback save also failed: {fallback_error}")
                return None

    def show_output_summary(self):
        """Show summary of output directory structure"""
        print(f"\n📁 OUTPUT DIRECTORY STRUCTURE:")
        print(f"   📂 Main folder: {self.output_dir}/")
        
        try:
            if os.path.exists(self.output_dir):
                # Show date subdirectories
                subdirs = [d for d in os.listdir(self.output_dir) if os.path.isdir(os.path.join(self.output_dir, d))]
                if subdirs:
                    subdirs.sort(reverse=True)  # Most recent first
                    print(f"   📅 Date folders:")
                    for subdir in subdirs[:3]:  # Show latest 3 dates
                        subdir_path = os.path.join(self.output_dir, subdir)
                        file_count = len([f for f in os.listdir(subdir_path) if f.endswith('.json')])
                        print(f"      • {subdir}/ ({file_count} reports)")
                    
                    if len(subdirs) > 3:
                        print(f"      • ... and {len(subdirs) - 3} more date folders")
                
                # Count total files
                total_files = 0
                for root, dirs, files in os.walk(self.output_dir):
                    total_files += len([f for f in files if f.endswith('.json')])
                
                print(f"   📊 Total reports: {total_files} JSON files")
            else:
                print(f"   ⚠️ Directory not found: {self.output_dir}")
                
        except Exception as e:
            print(f"   ⚠️ Error reading directory: {e}")

    def cleanup_old_reports(self, days_to_keep=30):
        """Clean up old report files (optional utility)"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = 0
            total_size_freed = 0
            
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size_freed += file_size
            
            if deleted_count > 0:
                size_mb = total_size_freed / (1024 * 1024)
                print(f"🧽 Cleaned up {deleted_count} old reports ({size_mb:.2f} MB freed)")
            else:
                print(f"🧽 No old reports to clean up (keeping {days_to_keep} days)")
                
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")


def main():
    """Main execution function"""
    print("🔍 Company Contact Finder - Integrated Tool")
    print("=" * 50)
    
    # Example usage with droplinked.com as requested
    company_domain = "droplinked.com"
    
    # You can change this to any company domain
    # company_domain = input("Enter company domain (e.g., droplinked.com): ").strip()
    
    if not company_domain:
        print("❌ No domain provided!")
        return
    
    # Create finder instance and run
    finder = CompanyContactFinder()
    results = finder.find_company_contacts(company_domain)
    
    # Save results to organized JSON structure
    json_file = finder.save_results_to_json()
    
    # Print formatted results
    print(f"\n📄 DETAILED RESULTS:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Show file organization summary
    finder.show_output_summary()
    
    if json_file:
        print(f"\n✅ Complete! Latest report saved to: {json_file}")
    else:
        print(f"\n⚠️ Report generation completed but file save failed")


if __name__ == "__main__":
    main()
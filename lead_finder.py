#!/usr/bin/env python3
# lead_finder.py

import os
import json
import time
import random
from playwright.sync_api import sync_playwright, Page, BrowserContext
from dotenv import load_dotenv
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from PIL import Image
import io
import base64

# --- Configuration ---
load_dotenv()

# Get cookie paths from .env file, using the same names as my existing files
GOOGLE_COOKIES_PATH = os.getenv("GOOGLE_COOKIES_PATH", "google-cookie.json")
# Add a placeholder for LinkedIn cookies, as they will be essential for scraping profiles
LINKEDIN_COOKIES_PATH = os.getenv("LINKEDIN_COOKIES_PATH", "linkedin_cookies.json") 

# OCR Configuration - Using docTR (Deep Learning OCR)
print("🔧 Initializing docTR OCR model...")
try:
    # Try a more robust model combination for web content
    print("🔧 Loading docTR model (db_resnet50 + parseq)...")
    ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='parseq', pretrained=True)
    print("✅ docTR OCR model (parseq) loaded successfully!")
except Exception as e:
    print(f"⚠️  Failed to load parseq model: {e}")
    try:
        print("🔧 Falling back to default model...")
        ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
        print("✅ docTR OCR model (crnn_vgg16_bn) loaded successfully!")
    except Exception as e2:
        print(f"❌ Failed to load any docTR model: {e2}")
        ocr_model = None

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

def cleanup_debug_screenshots(keep_recent=5):
    """Clean up old debug screenshots, keeping only the most recent ones"""
    try:
        screenshots_dir = "Screenshots"
        if not os.path.exists(screenshots_dir):
            return
            
        debug_files = [f for f in os.listdir(screenshots_dir) if f.startswith('debug_screenshot_') and f.endswith('.png')]
        if len(debug_files) > keep_recent:
            # Sort by modification time (newest first)
            debug_files.sort(key=lambda x: os.path.getmtime(os.path.join(screenshots_dir, x)), reverse=True)
            # Remove old files
            for old_file in debug_files[keep_recent:]:
                try:
                    os.remove(os.path.join(screenshots_dir, old_file))
                    print(f"🧹 Cleaned up old debug screenshot: {old_file}")
                except:
                    pass
    except Exception as e:
        print(f"⚠️  Could not cleanup debug screenshots: {e}")

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

def extract_search_data_with_ocr(page: Page, company_name: str) -> dict:
    """
    Takes a single full-page screenshot and extracts all search information using OCR.
    This function focuses on extracting data from Google search results page 1.
    """
    print(f"🔍 Starting OCR extraction for '{company_name}' search results...")
    
    try:
        # Wait for the page to fully load and handle any consent dialogs
        page.wait_for_timeout(3000)
        
        # Handle captcha and consent dialogs first
        if not handle_captcha_and_consent(page):
            print("❌ Failed to handle captcha/consent dialogs")
            return {"error": "Failed to handle captcha/consent"}
        
        # Wait for search results to appear
        try:
            page.wait_for_selector('div.g', timeout=10000)
            print("✅ Search results detected, proceeding with OCR...")
        except:
            print("⚠️  Search results selector not found, continuing anyway...")
        
        # Get page dimensions
        try:
            page_width = page.viewport_size['width']
            page_height = page.viewport_size['height']
        except (TypeError, KeyError):
            # Set default viewport size if not available
            page_width = 1920
            page_height = 1080
            print(f"⚠️  Using default viewport size: {page_width}x{page_height}")
        
        print(f"📏 Page dimensions: {page_width}x{page_height}")
        
        # Get the full page height
        print("📜 Getting full page height...")
        full_height = page.evaluate("""
            () => {
                return Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight
                );
            }
        """)
        
        print(f"📏 Full page height: {full_height}")
        
        # Take ONE full-page screenshot
        print("📸 Taking full-page screenshot...")
        screenshot = page.screenshot(full_page=True)
        print("✅ Full-page screenshot captured successfully!")
        
        # Save screenshot for debugging purposes in Screenshots folder
        debug_screenshot_path = f"Screenshots/debug_screenshot_{company_name}_{int(time.time())}.png"
        with open(debug_screenshot_path, "wb") as f:
            f.write(screenshot)
        print(f"💾 Screenshot saved for debugging: {debug_screenshot_path}")
        
        # Process the single screenshot with docTR
        try:
            if ocr_model is None:
                return {"error": "docTR OCR model not available"}
            
            # Convert screenshot to PIL Image
            image = Image.open(io.BytesIO(screenshot))
            print(f"📏 Screenshot dimensions: {image.size}")
            
            # Save image temporarily for docTR
            temp_image_path = "temp_screenshot.png"
            image.save(temp_image_path)
            
            # Create DocumentFile from the image
            doc = DocumentFile.from_images([temp_image_path])
            
            # Extract text using docTR OCR
            print("🔍 Running docTR OCR analysis...")
            result = ocr_model(doc)
            
            # Debug: Show what docTR detected
            print(f"📊 docTR detected {len(result.pages)} page(s)")
            for i, doc_page in enumerate(result.pages):
                print(f"   Page {i+1}: {len(doc_page.blocks)} blocks, {sum(len(block.lines) for block in doc_page.blocks)} lines")
                for j, block in enumerate(doc_page.blocks):
                    print(f"     Block {j+1}: {len(block.lines)} lines")
                    for k, line in enumerate(block.lines):
                        print(f"       Line {k+1}: {len(line.words)} words")
                        if len(line.words) > 0:
                            sample_words = [word.value for word in line.words[:3]]
                            print(f"         Sample words: {sample_words}")
            
            # Extract text from docTR results with better confidence handling
            extracted_text = ""
            confidence_threshold = 0.1  # Lower threshold to get more text
            
            for doc_page in result.pages:
                for block in doc_page.blocks:
                    for line in block.lines:
                        line_text = ""
                        for word in line.words:
                            # Include words with lower confidence to get more text
                            if hasattr(word, 'confidence') and word.confidence < confidence_threshold:
                                continue
                            line_text += word.value + " "
                        if line_text.strip():
                            extracted_text += line_text.strip() + "\n"
                    extracted_text += "\n"
            
            # If we still get very little text, try alternative extraction method
            if len(extracted_text.strip()) < 100:
                print("⚠️  Low text extraction, trying alternative method...")
                # Try to get all text regardless of confidence
                extracted_text = ""
                for doc_page in result.pages:
                    for block in doc_page.blocks:
                        for line in block.lines:
                            for word in line.words:
                                extracted_text += word.value + " "
                            extracted_text += "\n"
                        extracted_text += "\n"
            
            # Clean up temporary file
            try:
                os.remove(temp_image_path)
            except:
                pass
            
            if extracted_text.strip():
                print(f"✅ Text extracted: {len(extracted_text)} characters")
                
                # Extract structured information from the text
                extracted_data = extract_structured_info_from_text(extracted_text, company_name)
                
                # Extract links from the page using visual approach
                extracted_links = extract_links_visually(page)
                
                print(f"✅ docTR OCR extraction completed successfully!")
                print(f"📊 Extracted {len(extracted_data.get('results', []))} search results")
                print(f"🔗 Extracted {len(extracted_links)} links")
                
                return {
                    'company_name': company_name,
                    'total_screenshots': 1,
                    'total_text_length': len(extracted_text),
                    'extracted_data': extracted_data,
                    'extracted_links': extracted_links,
                    'raw_text': extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                    'ocr_method': 'docTR'
                }
            else:
                print("❌ No text extracted from screenshot")
                return {"error": "No text extracted from screenshot"}
                
        except Exception as e:
            print(f"❌ Error processing screenshot with docTR: {e}")
            return {"error": f"Error processing screenshot: {e}"}
        
    except Exception as e:
        print(f"❌ Error during OCR extraction: {e}")
        return {"error": str(e)}

def extract_links_visually(browser_page: Page) -> list:
    """Extract links by finding blue text and hovering to get URLs - much more reliable than CSS selectors!"""
    print("🔗 Extracting links using visual approach...")
    
    try:
        # Wait for page to fully load
        print("    ⏳ Waiting for page to load completely...")
        time.sleep(3)
        
        # Debug: Check page content
        print("    🔍 Checking page content...")
        try:
            page_title = browser_page.title()
            print(f"    📄 Page title: {page_title}")
        except:
            pass
        
        # Strategy 1: Find elements with blue text (Google's standard link color)
        print("    🎨 Looking for social media and email links...")
        blue_selectors = [
            'a[style*="color: rgb(26, 13, 171)"]',  # Google's blue link color
            'a[style*="color: #1a0dab"]',            # Hex version
            'a[style*="color: rgb(26, 13, 171)"]',  # RGB version
            'a[class*="link"]',                      # Generic link classes
            'a[href]'                                # Fallback to any link
        ]
        
        all_links = []
        for selector in blue_selectors:
            try:
                elements = browser_page.locator(selector).all()
                if elements:
                    print(f"    Found {len(elements)} elements with selector: {selector}")
                    for element in elements:
                        try:
                            # Get the text content
                            text = element.inner_text().strip()
                            if text and len(text) > 3:  # Only meaningful text
                                
                                # Get the href attribute directly (no need to hover)
                                href = element.get_attribute('href')
                                
                                # Only keep social media and email links
                                if href and href.startswith('http') and 'google.com' not in href:
                                    # Check if it's a social media profile or email
                                    is_social_or_email = any(site in href.lower() for site in [
                                        'linkedin.com/in/', 'instagram.com/', 'twitter.com/', 'x.com/',
                                        'facebook.com/', 'youtube.com/', 'tiktok.com/'
                                    ]) or '@' in href
                                    
                                    if is_social_or_email:
                                        all_links.append({
                                            'text': text,
                                            'url': href,
                                            'element': element
                                        })
                                    
                        except Exception as e:
                            continue
                            
            except Exception as e:
                continue
        
        # Strategy 2: Find any clickable elements by looking for cursor changes
        print("    🖱️  Looking for clickable elements...")
        try:
            # Find elements that change cursor on hover
            clickable_elements = browser_page.locator('a[href], button, [role="button"], [tabindex]').all()
            print(f"    Found {len(clickable_elements)} potentially clickable elements")
            
            for element in clickable_elements:
                try:
                    # Get the text content
                    text = element.inner_text().strip()
                    if text and len(text) > 3:
                        
                        # Get href if it's a link (no need to hover)
                        href = element.get_attribute('href')
                        if href and href.startswith('http') and 'google.com' not in href:
                            # Check if we already have this URL
                            if not any(link['url'] == href for link in all_links):
                                all_links.append({
                                    'text': text,
                                    'url': href,
                                    'element': element
                                })
                                
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ⚠️  Error in clickable element detection: {e}")
        
        # Strategy 3: Look for URL patterns in the page content
        print("    🔍 Looking for URL patterns in page content...")
        try:
            page_content = browser_page.content()
            # Simple regex to find URLs
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls_in_content = re.findall(url_pattern, page_content)
            
            print(f"    Found {len(urls_in_content)} URLs in page content")
            
            # Filter out Google URLs and duplicates
            unique_urls = []
            for url in urls_in_content:
                if 'google.com' not in url and url not in unique_urls:
                    unique_urls.append(url)
            
            # Try to find the text associated with these URLs
            for url in unique_urls[:10]:  # Limit to first 10
                try:
                    # Look for elements that might contain this URL
                    url_elements = browser_page.locator(f'a[href*="{url.split("//")[1].split("/")[0]}"]').all()
                    for element in url_elements:
                        text = element.inner_text().strip()
                        if text and len(text) > 3:
                            if not any(link['url'] == url for link in all_links):
                                all_links.append({
                                    'text': text,
                                    'url': url,
                                    'element': element
                                })
                                break
                except:
                    continue
                    
        except Exception as e:
            print(f"    ⚠️  Error in URL pattern detection: {e}")
        
        print(f"    📊 Total potential links found: {len(all_links)}")
        
        # Extract final link information
        extracted_links = []
        for link in all_links:
            try:
                                 # Classify the link type
                 is_linkedin = 'linkedin.com/in/' in link['url']
                 is_instagram = 'instagram.com/' in link['url']
                 is_twitter = 'twitter.com/' in link['url'] or 'x.com/' in link['url']
                 is_email = '@' in link['url']
                 is_social = any(site in link['url'] for site in ['linkedin.com/in/', 'instagram.com/', 'twitter.com/', 'x.com/', 'facebook.com/', 'youtube.com/', 'tiktok.com/'])
                 
                 extracted_links.append({
                     'url': link['url'],
                     'text': link['text'],
                     'title': '',  # Could be enhanced later
                     'is_linkedin': is_linkedin,
                     'is_instagram': is_instagram,
                     'is_twitter': is_twitter,
                     'is_email': is_email,
                     'is_social': is_social
                 })
            except Exception as e:
                continue
        
        # Remove duplicates based on URL
        unique_links = []
        seen_urls = set()
        for link in extracted_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"✅ Extracted {len(unique_links)} unique links using visual approach")
        
        # Debug: Show some sample links
        if unique_links:
            print("    📋 Sample links:")
            for i, link in enumerate(unique_links[:5]):
                profile_icon = "👤" if link['is_profile'] else "🔗"
                print(f"      {i+1}. {profile_icon} {link['text'][:50]}... -> {link['url']}")
        
        return unique_links
        
    except Exception as e:
        print(f"❌ Error in visual link extraction: {e}")
        return []

def extract_structured_info_from_text(text: str, company_name: str) -> dict:
    """
    Extracts structured information from OCR text.
    Parses Google search results to find company names, titles, and other relevant information.
    """
    print("🔍 Parsing extracted text for structured information...")
    
    lines = text.split('\n')
    results = []
    
    # Look for patterns that indicate search results
    current_result = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for company names or titles
        if company_name.lower() in line.lower():
            if current_result:
                results.append(current_result)
            current_result = {'company': line, 'title': '', 'description': ''}
            
        # Look for titles (CEO, Founder, CTO, etc.)
        elif any(title in line.lower() for title in ['ceo', 'founder', 'cto', 'cfo', 'coo', 'president', 'director', 'manager']):
            if current_result:
                current_result['title'] = line
                
        # Look for descriptions or additional info
        elif len(line) > 20 and not current_result.get('description'):
            if current_result:
                current_result['description'] = line
    
    # Add the last result if it exists
    if current_result:
        results.append(current_result)
    
    # If no structured results found, try to extract any company-related information
    if not results:
        company_mentions = []
        for line in lines:
            if company_name.lower() in line.lower():
                company_mentions.append(line)
        
        if company_mentions:
            results = [{'company': mention, 'title': '', 'description': ''} for mention in company_mentions]
    
    return {
        'results': results,
        'total_results': len(results),
        'company_name': company_name
    }

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
        
        # --- Step 1: Google Search with OCR Extraction ---
        print("--- Phase 1: Google Search with OCR Data Extraction ---")
        google_page = context.new_page()
        load_cookies(context, GOOGLE_COOKIES_PATH)
        
        # Navigate to Google search with targeted social media and email queries
        # Focus ONLY on social profiles and contact information
        search_queries = [
            # Social Media Profiles
            f'"{target_company}" CEO OR founder OR executive site:linkedin.com/in/',
            f'"{target_company}" CEO OR founder OR executive site:instagram.com/',
            f'"{target_company}" CEO OR founder OR executive site:twitter.com/',
            f'"{target_company}" CEO OR founder OR executive site:x.com/',
            
            # Contact Information
            f'"{target_company}" email OR contact OR "@"',
            f'"{target_company}" contact@ OR info@ OR hello@ OR support@'
        ]
        
        all_leads_data = []
        
        # Process each search query with short delays
        for query_num, search_query in enumerate(search_queries, 1):
            print(f"\n🔍 Search Query {query_num}/{len(search_queries)}: {search_query}")
            print(f"📊 Executing targeted social media and email search...")
            
            try:
                google_page.goto(f"https://www.google.com/search?q={search_query}", wait_until="domcontentloaded")
                
                # Add HUMAN-LIKE page interaction before OCR
                print("👤 Simulating human page interaction...")
                
                # Random scroll down and up (like reading)
                scroll_down = random.randint(2, 5)
                for _ in range(scroll_down):
                    google_page.evaluate("window.scrollBy(0, 300)")
                    time.sleep(random.uniform(0.5, 1.5))
                
                # Random scroll back up
                scroll_up = random.randint(1, 3)
                for _ in range(scroll_up):
                    google_page.evaluate("window.scrollBy(0, -200)")
                    time.sleep(random.uniform(0.3, 1.0))
                
                # Random mouse movement simulation
                print("🖱️  Simulating natural mouse movements...")
                time.sleep(random.uniform(2, 4))
                
                # Extract data using OCR
                ocr_results = extract_search_data_with_ocr(google_page, target_company)
                
                if "error" not in ocr_results:
                    print("✅ OCR extraction successful!")
                    print(f"📊 Found {ocr_results['total_screenshots']} screenshots")
                    print(f"📝 Extracted {ocr_results['total_text_length']} characters of text")
                    print(f"🏢 Found {ocr_results['extracted_data']['total_results']} potential results")
                    print(f"🔗 Found {len(ocr_results.get('extracted_links', []))} links")
                    
                    # Display extracted results
                    print("\n📋 Extracted Information:")
                    for j, result in enumerate(ocr_results['extracted_data']['results'], 1):
                        print(f"  {j}. Company: {result.get('company', 'N/A')}")
                        print(f"     Title: {result.get('title', 'N/A')}")
                        print(f"     Description: {result.get('description', 'N/A')}")
                        print()
                    
                    # Display extracted links
                    if ocr_results.get('extracted_links'):
                        print("🔗 Extracted Social Media & Email Links:")
                        for j, link in enumerate(ocr_results['extracted_links'][:10], 1):  # Show first 10 links
                            # Choose appropriate icon based on link type
                            if link['is_linkedin']:
                                icon = "💼 LinkedIn"
                            elif link['is_instagram']:
                                icon = "📸 Instagram"
                            elif link['is_twitter']:
                                icon = "🐦 X/Twitter"
                            elif link['is_email']:
                                icon = "📧 Email"
                            elif link['is_social']:
                                icon = "🌐 Social"
                            else:
                                icon = "🔗 Link"
                            
                            print(f"  {j}. {icon}: {link['text'][:50]}...")
                            print(f"     {link['url']}")
                            if link['title']:
                                print(f"     📝 {link['title'][:100]}...")
                            print()
                    
                    all_leads_data.append(ocr_results)
                else:
                    print(f"❌ OCR extraction failed: {ocr_results['error']}")
                    
            except Exception as e:
                print(f"❌ Error during search query {query_num}: {e}")
                continue
            
            # Add short delays between queries (5-8 seconds)
            if query_num < len(search_queries):
                delay = random.uniform(5, 8)
                print(f"⏳ Waiting {delay:.1f} seconds before next query...")
                time.sleep(delay)
        
        # --- Step 2: Display Final Results ---
        print("\n--- Final Results Summary ---")
        if all_leads_data:
            print("✅ Data extraction completed successfully!")
            print(f"📊 Total searches executed: {len(all_leads_data)}")
            # Count total unique links
            all_urls = set()
            for data in all_leads_data:
                for link in data.get('extracted_links', []):
                    all_urls.add(link['url'])
            print(f"🔗 Total unique links found: {len(all_urls)}")
            print(f"📝 Total text extracted: {sum(data.get('total_text_length', 0) for data in all_leads_data)} characters")
            
            # Display summary of all results
            print("\n📋 Summary of All Extracted Data:")
            for i, data in enumerate(all_leads_data, 1):
                print(f"  Search {i}: {data.get('extracted_data', {}).get('total_results', 0)} results, {len(data.get('extracted_links', []))} links")
            
            print("\n📄 Full JSON Results:")
            print(json.dumps(all_leads_data, indent=2))
        else:
            print("❌ No data was extracted from any search queries.")
        
        google_page.close()
        
        # Clean up old debug screenshots (keep only the 5 most recent)
        print("\n🧹 Cleaning up old debug screenshots...")
        cleanup_debug_screenshots(keep_recent=5)

        browser.close()

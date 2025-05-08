#!/usr/bin/env python3
# domain_contact_scraper.py

import os
import re
import csv
import time
import json
import traceback
import requests
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import io # For reading CSV from URL

# --- Load environment variables from .env file ---
load_dotenv()

# --- Configuration ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

GOOGLE_SHEET_WORKER_URL = os.environ.get("GOOGLE_SHEET_WORKER_URL") # For /sheet-request

# Define social media domains and mappings
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

# --- Regex Patterns ---
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d{1,4}[-.\s()]?)?\(?\d{2,4}\)?[-.\s()]?\d{2,4}[-.\s()]?\d{2,5}"
MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 17
FLOAT_COORD_PATTERN = re.compile(r"^\d+(\.\d+)?\s+\d+\.\d+$")
SIMPLE_FLOAT_PATTERN = re.compile(r"^\d+\.\d+$")

# --- CSV Field Names ---
CSV_FIELDS = ['Domain', 'Emails', 'Phone Numbers', 'Instagram', 'LinkedIn', 'X', 'Facebook', 'Other Socials']
CSV_OUTPUT_FOLDER = 'output_csvs'

# --- Flask App Setup ---
app = Flask(__name__)

# --- Helper Functions ---

def get_api_key():
    key = os.environ.get("MY_API_SECRET")
    if not key:
        print("CRITICAL: MY_API_SECRET environment variable not found.")
    return key

def authenticate_request(request_obj):
    api_key = request_obj.headers.get('api-key')
    expected_key = get_api_key()
    if not expected_key:
        return False, jsonify({"error": "Server configuration error: API key not set"}), 500
    if not api_key or api_key != expected_key:
        return False, jsonify({"error": "Unauthorized"}), 401
    return True, None, None

def categorize_social_link(url):
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

def is_plausible_phone_candidate(candidate_str_orig, min_digits=MIN_PHONE_DIGITS, max_digits=MAX_PHONE_DIGITS):
    candidate_str = candidate_str_orig.strip()

    if not candidate_str or len(candidate_str) < min_digits - 4:
        return False

    # --- Stage 1: Reject obvious non-phone patterns ---
    if re.fullmatch(r"\d{1,2}[-/. ]\d{1,2}[-/. ]\d{2,4}", candidate_str): return False
    if re.fullmatch(r"\d{4}[-/. ]\d{1,2}[-/. ]\d{1,2}", candidate_str): return False
    if re.fullmatch(r"\d{4}\s?-\s?\d{4}", candidate_str): return False
    if re.fullmatch(r"\(\s?\d{4}\s?-\s?\d{4}\s?\)", candidate_str): return False
    
    if re.fullmatch(r"\d+\.\d+\s+\d+", candidate_str): return False
    if re.fullmatch(r"\d\.\d+\s+\d+", candidate_str): return False

    if (SIMPLE_FLOAT_PATTERN.match(candidate_str) or FLOAT_COORD_PATTERN.match(candidate_str)):
        if not re.search(r"[\-()]", candidate_str) or \
           (candidate_str.count('-') == 1 and candidate_str.startswith('-') and candidate_str.count('.') > 0):
            return False

    # --- Stage 2: Digit count and basic properties ---
    digits_only = "".join(filter(str.isdigit, candidate_str))
    num_digits = len(digits_only)

    if not (min_digits <= num_digits <= max_digits):
        return False

    if len(set(digits_only)) == 1 and num_digits >= 7:
        return False
    
    if digits_only.startswith('000000') and num_digits <= 8:
        return False

    # --- Stage 3: Unformatted numbers ---
    is_purely_numeric_str = candidate_str.replace('.', '').isdigit()
    
    if is_purely_numeric_str and not candidate_str.startswith('+') and not re.search(r"[\s\-()]", candidate_str):
        if num_digits == 10:
            try:
                val = int(digits_only)
                if 946684800 <= val <= 2051222400:
                    return False
            except ValueError: pass
        if num_digits not in [7, 10, 11]:
            return False
    
    # --- Stage 4: Check for non-phone letters ---
    temp_cleaned_for_letters = re.sub(r"[\d\s\-().+]", "", candidate_str.lower())
    temp_cleaned_for_letters = re.sub(r"extn?\.?|ext|x", "", temp_cleaned_for_letters).strip()
    if re.search(r"[a-wya-z]", temp_cleaned_for_letters):
        return False

    # --- Stage 5: Segment analysis for ID-like patterns ---
    segments = re.split(r"[\s-]+", candidate_str.replace('(', '').replace(')', '').replace('.', ''))
    segments = [s for s in segments if s.strip() and s.isdigit()]

    if not segments: return False

    if len(segments) >= 2:
        if segments[0] == '0' and len(segments) >= 3:
            if all(1 <= len(seg) <= 4 for seg in segments[1:]):
                return False
        
        if len(segments) == 2 and not re.search(r"[\()]", candidate_str):
            len1, len2 = len(segments[0]), len(segments[1])
            if num_digits <= 8:
                if ((3 <= len1 <= 4 and 1 <= len2 <= 3) or \
                    (1 <= len1 <= 3 and 3 <= len2 <= 4)):
                    if candidate_str.count('.') <=1 :
                        return False

        if candidate_str.count('-') == 1 and not re.search(r"[\s()+.]", candidate_str) and len(segments) == 2:
            len1, len2 = len(segments[0]), len(segments[1])
            if ((len1 >= 5 and 1 <= len2 <= 4) or (len2 >= 5 and 1 <= len1 <= 4)):
                 if num_digits >=8:
                    return False
        if len(segments) == 3 and candidate_str.count('-') == 2: # e.g. 500813-1713-47
            if len(segments[0]) >=5 and len(segments[1]) <=4 and len(segments[2]) <=2:
                return False


    # --- Stage 6: Final structural checks ---
    if candidate_str.startswith('(') and ')' not in candidate_str:
        if not re.search(r"\(\d{3,4}\)\s?\d", candidate_str):
             return False
             
    return True

def normalize_url(url):
    """Normalize URL to get the landing page URL."""
    if not url:
        return None, None
        
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        # Make a HEAD request to check for redirects
        response = requests.head(url, allow_redirects=True, timeout=10)
        final_url = response.url
        
        # Parse the URL to get the base domain
        parsed = urlparse(final_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        display_url = parsed.netloc
        if display_url.startswith("www."):
            display_url = display_url[4:]
        
        return base_url, display_url
    except Exception as e:
        print(f"Error normalizing URL {url}: {e}")
        return None, None

def extract_logo_url(soup, base_url):
    """Extract the logo URL from the webpage with improved validation."""
    # Try to get the base domain for relative URLs
    try:
        parsed_url = urlparse(base_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    except:
        base_domain = base_url

    def normalize_url(url):
        """Convert relative URLs to absolute URLs."""
        if not url:
            return None
        if not url.startswith(('http://', 'https://')):
            return base_domain + ('/' if not url.startswith('/') else '') + url
        return url

    def is_likely_logo(img_element):
        """Validate if an image element is likely to be a logo."""
        if not img_element:
            return False
            
        # Check image dimensions (logos are typically square-ish and not too large)
        width = img_element.get('width')
        height = img_element.get('height')
        if width and height:
            try:
                w = int(width)
                h = int(height)
                # Logos are typically not too large and maintain reasonable aspect ratio
                if w > 500 or h > 500 or (w > 0 and h > 0 and (w/h > 3 or h/w > 3)):
                    return False
            except ValueError:
                pass

        # Check if image is in header/navbar
        parent = img_element.parent
        while parent:
            parent_class = parent.get('class', [])
            parent_id = parent.get('id', '')
            if any(x in str(parent_class).lower() or x in str(parent_id).lower() 
                  for x in ['header', 'navbar', 'nav', 'brand', 'logo']):
                return True
            parent = parent.parent

        return False

    # 1. Check for favicon/shortcut icon (most reliable for brand identity)
    favicon = soup.find('link', rel=lambda x: x and ('icon' in x.lower() or 'shortcut' in x.lower()))
    if favicon and favicon.get('href'):
        return normalize_url(favicon['href'])

    # 2. Check for og:image meta tag (usually the main brand image)
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return normalize_url(og_image['content'])

    # 3. Look for logo in header/navbar first
    header = soup.find(['header', 'nav'], class_=lambda x: x and any(term in str(x).lower() 
                                                                     for term in ['header', 'navbar', 'nav']))
    if header:
        # Look for images with logo-related attributes
        logo_img = header.find('img', 
                             attrs={'alt': lambda x: x and any(term in str(x).lower() 
                                                             for term in ['logo', 'brand'])})
        if logo_img and logo_img.get('src'):
            return normalize_url(logo_img['src'])

    # 4. Look for images with specific logo-related attributes
    logo_patterns = [
        'logo', 'brand', 'header-logo', 'site-logo', 'company-logo',
        'navbar-logo', 'nav-logo', 'header-brand', 'site-brand'
    ]
    
    for pattern in logo_patterns:
        # Check by ID
        logo_img = soup.find('img', id=lambda x: x and pattern in str(x).lower())
        if logo_img and is_likely_logo(logo_img) and logo_img.get('src'):
            return normalize_url(logo_img['src'])
            
        # Check by class
        logo_img = soup.find('img', class_=lambda x: x and pattern in str(x).lower())
        if logo_img and is_likely_logo(logo_img) and logo_img.get('src'):
            return normalize_url(logo_img['src'])

    # 5. As a last resort, look for the first image in the header that might be a logo
    if header:
        for img in header.find_all('img'):
            if is_likely_logo(img) and img.get('src'):
                return normalize_url(img['src'])

    return None

def wait_for_page_load(driver, timeout=20):
    """Wait for the page to be fully loaded."""
    try:
        # Wait for document ready state
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # Wait for all links to be present
        WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
        )
        
        return True
    except Exception as e:
        print(f"Page load wait error: {str(e)[:200]}")
        return False

def scrape_domain(domain_input):
    original_domain_input = domain_input
    driver = None
    try:
        processed_url, display_domain = normalize_url(domain_input)
        if not processed_url:
            return {"error": "Invalid or unreachable URL"}, 400

        print(f"\n--- Processing Domain: {display_domain} (from {original_domain_input}) ---")
        
        social_links = {}
        emails_found = set()
        phones_found = set()
        
        default_result_on_error = {"error": f"Error processing domain: {display_domain} (from {original_domain_input})"}, 500
        
        try:
            driver_path = os.environ.get("DRIVER_PATH")
            if driver_path:
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            
            # Set memory-related options
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)
            
            # Clear browser cookies before loading
            driver.delete_all_cookies()
            
            driver.get(processed_url)
            
            try:
                if not wait_for_page_load(driver):
                    print(f"Page load timeout for {display_domain}, proceeding with available content.")
            except TimeoutException:
                print(f"Page load timeout for {display_domain}, proceeding with available content.")
            
            page_source = driver.page_source
            if not page_source:
                print(f"Warning: Empty page source for {display_domain}")
                return default_result_on_error
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Clear page source to free memory
            page_source = None
            
            # --- Email and Social Link Extraction (from whole page) ---
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if not href or not isinstance(href, str): continue
                href = href.strip()
                if not href: continue
                
                # EMAILS from mailto:
                if href.startswith('mailto:'):
                    try:
                        email_part = unquote(href.split('mailto:', 1)[1].split('?')[0]).strip()
                        if re.fullmatch(EMAIL_REGEX, email_part):
                            emails_found.add(email_part)
                    except Exception: pass
                    continue # Processed as mailto, move to next link
                
                # PHONES from tel: (apply plausibility check)
                if href.startswith('tel:'):
                    try:
                        phone_part = href.split('tel:', 1)[1].strip()
                        if is_plausible_phone_candidate(phone_part, min_digits=6, max_digits=20):
                            phones_found.add(phone_part) 
                    except Exception: pass
                    # Even if it's a tel link, it might also be a social link (e.g. whatsapp)
                    # So we don't 'continue' here necessarily, let social check run
                
                # SOCIAL MEDIA links
                try:
                    abs_href = href
                    parsed_original_url = urlparse(processed_url) # Use the selenium-loaded URL context
                    if not abs_href.startswith(('http://', 'https://')):
                        if abs_href.startswith('//'):
                            abs_href = (parsed_original_url.scheme or 'https') + ':' + abs_href
                        elif abs_href.startswith('/'):
                            base_url = f"{(parsed_original_url.scheme or 'https')}://{parsed_original_url.netloc}"
                            abs_href = f"{base_url}{abs_href}"
                        else:
                            abs_href = (parsed_original_url.scheme or 'https') + '://' + abs_href
                        # else: 
                        #     # If it's not absolute, and not starting with // or /, it might be a malformed or relative link
                        #     # that's not easily resolvable to a social media URL. Skip for social check.
                        #     if social_type == "other": continue # Only skip if we haven't already ID'd it from tel:
                    
                    social_type, social_url = categorize_social_link(abs_href)
                    if social_type and social_type not in social_links : # Store first one found per type
                        social_links[social_type] = social_url
                except Exception:
                    pass # Ignore errors in social link categorization
            
            # Clear links list to free memory
            all_links = None
            
            # Emails from page text
            if soup.body:
                try:
                    body_text_for_emails = soup.body.get_text(separator=' ', strip=True)
                    emails_found.update(re.findall(EMAIL_REGEX, body_text_for_emails))
                except Exception: pass

            # --- Phone Number Extraction (focused on footer from text) ---
            footer_text_content = ""
            # Try to find <footer> tag first
            footer_elements = soup.find_all('footer')
            if not footer_elements: # If no <footer>, try common class/id selectors
                footer_elements = soup.select('.footer, #footer, [class*="site-footer"], [id*="site-footer"], [role="contentinfo"]')
            
            if footer_elements:
                # print(f"Found {len(footer_elements)} potential footer element(s) for {display_domain}.")
                for footer_el in footer_elements:
                    footer_text_content += footer_el.get_text(separator=' ', strip=True) + " "
            else:
                print(f"No distinct footer element found for {display_domain}. Text-based phone search will be skipped for this domain.")
                # If you want to fallback to body if no footer, uncomment below.
                # This can be very noisy.
                # if soup.body:
                #     footer_text_content = soup.body.get_text(separator=' ', strip=True)
                #     print(f"Warning: Searching entire body for phones on {display_domain} as no footer found.")

            # Clear footer elements to free memory
            footer_elements = None

            if footer_text_content: # Only search for phones in text if footer content was found
                try:
                    candidate_phone_strings_footer = set()
                    for match in re.finditer(PHONE_REGEX, footer_text_content):
                        candidate_phone_strings_footer.add(match.group(0).strip())
                    
                    for text_match_str in candidate_phone_strings_footer:
                        if is_plausible_phone_candidate(text_match_str):
                            phones_found.add(text_match_str)
                        # else: # For debugging
                            # print(f"Footer Filtered: '{text_match_str}' for {display_domain}")
                except Exception as e:
                    print(f"Error regex-finding/filtering phones in footer for {display_domain}: {e}")
            
            # Clear footer text to free memory
            footer_text_content = None
            
            # Extract logo URL
            try:
                logo_url = extract_logo_url(soup, processed_url)
            except Exception as e:
                print(f"Error extracting logo URL for {display_domain}: {e}")
                logo_url = None
            
            # Clear soup to free memory
            soup = None
            
            result = {
                'domain': processed_url,
                'logoURL': logo_url,
                'socialLinks': social_links,
                'emails': sorted(list(emails_found)),
                'phones': sorted(list(set(phones_found)))
            }
            
            print(f"Extraction complete for {display_domain}: {len(emails_found)} emails, {len(phones_found)} plausible phones, {len(social_links)} distinct social categories.")
            return result, 200
            
        except WebDriverException as e:
            print(f"WebDriverException for {display_domain}: {str(e)[:200]}")
        except TimeoutException:
            print(f"Page load timeout for {display_domain}")
        except Exception as e:
            print(f"Error processing {display_domain}: {e}")
            traceback.print_exc()
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Error closing WebDriver for {display_domain}: {e}")
                driver = None
        
        return default_result_on_error

    except Exception as e:
        print(f"Outer unexpected error for input '{original_domain_input}': {e}")
        traceback.print_exc()
        return default_result_on_error

# The rest of the functions (generate_csv_file, _process_domain_list_and_generate_csv, Flask routes)
# remain the same as in the previous response.

def generate_csv_file(results, base_filename_prefix="scraped_data"):
    if not os.path.exists(CSV_OUTPUT_FOLDER):
        os.makedirs(CSV_OUTPUT_FOLDER)
    
    timestamp = int(time.time())
    csv_filename_only = f"{base_filename_prefix}_{timestamp}.csv"
    csv_filepath = os.path.join(CSV_OUTPUT_FOLDER, csv_filename_only)
    
    try:
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(CSV_FIELDS)
            
            for result in results:
                writer.writerow([
                    str(result.get('domain', '')),
                    '; '.join(result.get('emails', [])),
                    '; '.join(result.get('phones', [])),
                    str(result.get('instagram', '')),
                    str(result.get('linkedin', '')),
                    str(result.get('x', '')),
                    str(result.get('facebook', '')),
                    '; '.join(result.get('other', []))
                ])
        return csv_filename_only
    except IOError as io_err:
        print(f"IOError writing CSV file {csv_filepath}: {io_err}")
    except Exception as csv_err:
        print(f"General error writing CSV file {csv_filepath}: {csv_err}")
        traceback.print_exc()
    return None


def _process_domain_list_and_generate_csv(domains_list, max_workers, csv_file_prefix, generate_csv=True):
    results = []
    valid_domains = [str(d).strip() for d in domains_list if d and isinstance(d, str) and str(d).strip()]
    
    if not valid_domains:
        return [], None, "No valid domains provided for processing."

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {executor.submit(scrape_domain, domain): domain for domain in valid_domains}
        for _, future in enumerate(future_to_domain):
            domain_name = future_to_domain[future]
            try:
                result, _ = future.result()
                results.append(result)
            except Exception as e:
                print(f"Exception processing domain {domain_name} in thread: {e}")
                results.append({"error": f"Error processing domain: {domain_name}"})
    
    csv_filename = generate_csv_file(results, csv_file_prefix) if generate_csv else None
    return results, csv_filename, f"Processed {len(results)} domains." if csv_filename or not generate_csv else "Processed domains, but CSV generation failed."


# --- API Endpoints ---

@app.route('/single-request', methods=['POST'])
def single_request():
    authenticated, response, status_code = authenticate_request(request)
    if not authenticated:
        return response, status_code

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    
    target_url = data['url']
    if not isinstance(target_url, str) or not target_url.strip():
        return jsonify({"error": "Invalid 'url' provided"}), 400

    print(f"\n--- Single Request: {target_url} ---")
    
    result, status_code = scrape_domain(target_url)
    if "error" in result or status_code != 200:
        return jsonify(result), status_code or 500
    
    results_list = [result]
    
    csv_filename = generate_csv_file(results_list, "single_domain")
    
    return jsonify({
        "success": True,
        "message": f"Processed 1 domain. CSV {'generated' if csv_filename else 'generation failed'}.",
        "csv_filename": csv_filename,
        "results": results_list
    }), 200


@app.route('/array-request', methods=['POST'])
def array_request():
    authenticated, response, status_code = authenticate_request(request)
    if not authenticated:
        return response, status_code

    data = request.get_json()
    if not data or 'domains' not in data:
        return jsonify({"error": "Missing 'domains' array in request body"}), 400
    
    domains_list = data['domains']
    if not isinstance(domains_list, list):
        return jsonify({"error": "'domains' must be an array"}), 400
        
    max_workers = data.get('max_workers', 5)
    try:
        max_workers = int(max_workers)
        if not (1 <= max_workers <= 20): max_workers = 5
    except (ValueError, TypeError):
        max_workers = 5

    generate_csv = data.get('generate_csv', True)
    if not isinstance(generate_csv, bool):
        generate_csv = True

    print(f"\n--- Array Request: {len(domains_list)} domains, {max_workers} workers, CSV generation: {generate_csv} ---")
    
    results, csv_filename, message = _process_domain_list_and_generate_csv(domains_list, max_workers, "array_domains", generate_csv)
    
    response_data = {
        "success": True if results else False,
        "message": message,
        "results": results
    }
    
    if generate_csv:
        response_data["csv_filename"] = csv_filename
    
    return jsonify(response_data), 200


@app.route('/csv-request', methods=['POST'])
def csv_request():
    authenticated, response, status_code = authenticate_request(request)
    if not authenticated:
        return response, status_code

    data = request.get_json()
    if not data or 'csv_url' not in data:
        return jsonify({"error": "Missing 'csv_url' in request body"}), 400
    
    csv_url = data['csv_url']
    domain_column_header = data.get('domain_column_header', None) 
    max_workers = data.get('max_workers', 5)
    try:
        max_workers = int(max_workers)
        if not (1 <= max_workers <= 20): max_workers = 5
    except (ValueError, TypeError):
        max_workers = 5

    print(f"\n--- CSV Request: {csv_url}, column header: '{domain_column_header if domain_column_header else 'Not specified (use first column)'}', {max_workers} workers ---")
    
    domains_list = []
    try:
        req_response = requests.get(csv_url, timeout=30)
        req_response.raise_for_status()
        
        csv_content = req_response.content.decode('utf-8-sig')
        csvfile = io.StringIO(csv_content)
        reader = csv.reader(csvfile)
        
        if domain_column_header: 
            header = next(reader, None)
            if not header:
                return jsonify({"error": "CSV file is empty or has no header row when 'domain_column_header' is specified"}), 400
            
            try:
                domain_col_idx = header.index(domain_column_header)
            except ValueError:
                return jsonify({"error": f"Specified 'domain_column_header' ('{domain_column_header}') not found in CSV header: {', '.join(header)}"}), 400
            
            for row_number, row in enumerate(reader, start=1): 
                if len(row) > domain_col_idx and row[domain_col_idx].strip():
                    domains_list.append(row[domain_col_idx].strip())

        else: 
            domain_col_idx = 0
            for row_number, row in enumerate(reader): 
                if row and len(row) > domain_col_idx and row[domain_col_idx].strip():
                    domains_list.append(row[domain_col_idx].strip())
            
        if not domains_list:
            return jsonify({"error": "No domains extracted from the CSV based on the provided criteria"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download CSV: {str(e)}"}), 500
    except csv.Error as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 500
    except Exception as e:
        print(f"Error processing CSV request: {e}")
        traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred while processing CSV: {str(e)}"}), 500

    results, csv_filename, message = _process_domain_list_and_generate_csv(domains_list, max_workers, "csv_import_domains")
    
    return jsonify({
        "success": True if csv_filename or results else False,
        "message": f"{message} Extracted {len(domains_list)} domain(s) from CSV.",
        "csv_filename": csv_filename,
        "results": results
    }), 200


@app.route('/sheet-request', methods=['POST'])
def sheet_request():
    authenticated, response, status_code = authenticate_request(request)
    if not authenticated:
        return response, status_code

    if not GOOGLE_SHEET_WORKER_URL:
        print("ERROR: GOOGLE_SHEET_WORKER_URL environment variable not set.")
        return jsonify({"error": "Server configuration error: Google Sheet worker URL not configured."}), 500

    data = request.get_json()
    if not data or 'target_url' not in data:
        return jsonify({"error": "Missing 'target_url' in request body"}), 400
    
    target_url = data['target_url']
    max_workers = data.get('max_workers', 5)
    try:
        max_workers = int(max_workers)
        if not (1 <= max_workers <= 20): max_workers = 5
    except (ValueError, TypeError):
        max_workers = 5

    print(f"\n--- Sheet Request: (using configured worker), target {target_url}, {max_workers} workers ---")
    
    domains_list = []
    try:
        worker_response = requests.post(GOOGLE_SHEET_WORKER_URL, json={"url": target_url}, timeout=60)
        worker_response.raise_for_status()
        
        worker_data = worker_response.json()
        if not worker_data.get('success'):
            err_msg = worker_data.get('message', 'Worker reported failure')
            print(f"Worker error: {err_msg}")
            return jsonify({"error": f"Worker failed: {err_msg}"}), 500
        
        domains_list = worker_data.get('domains', [])
        if not domains_list or not isinstance(domains_list, list):
            print(f"No domains returned from worker or invalid format: {domains_list}")
            return jsonify({"error": "No domains returned from worker or format is invalid"}), 400
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with worker: {e}")
        return jsonify({"error": f"Could not connect to worker: {str(e)}"}), 500
    except json.JSONDecodeError:
        print(f"Error decoding JSON from worker. Response text: {worker_response.text[:200]}")
        return jsonify({"error": "Invalid JSON response from worker"}), 500
    except Exception as e:
        print(f"Error in sheet request setup: {e}")
        traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    results, csv_filename, message = _process_domain_list_and_generate_csv(domains_list, max_workers, "sheet_import_domains")
    
    return jsonify({
        "success": True if csv_filename or results else False,
        "message": f"{message} Received {len(domains_list)} domain(s) from sheet worker.",
        "csv_filename": csv_filename,
        "results": results
    }), 200


@app.route('/download-csv/<filename>', methods=['GET'])
def download_csv(filename):
    authenticated, response, status_code = authenticate_request(request)
    if not authenticated:
        return response, status_code
    
    if '..' in filename or filename.startswith(('/', '\\')):
        return jsonify({"error": "Invalid filename"}), 400
    
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(CSV_OUTPUT_FOLDER, safe_filename)
    
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found. It might have been cleaned up or never created."}), 404
        
    try:
        return send_file(filepath, 
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=safe_filename)
    except Exception as e:
        print(f"Error downloading CSV file {safe_filename}: {e}")
        return jsonify({"error": f"Error downloading CSV file: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "active"}), 200

# --- Run the Flask App ---
if __name__ == '__main__':
    if not os.path.exists(CSV_OUTPUT_FOLDER):
        os.makedirs(CSV_OUTPUT_FOLDER)
    if not get_api_key():
        print("FATAL: MY_API_SECRET environment variable is not set.")
    if not GOOGLE_SHEET_WORKER_URL:
        print("WARNING: GOOGLE_SHEET_WORKER_URL environment variable is not set. /sheet-request endpoint will not function.")
    
    # Set debug=False when deploying to production
    debug = (os.environ.get("DEBUG") == "True")
    app.run(host='0.0.0.0', port=5000, debug=debug)

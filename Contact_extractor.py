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

# --- Load environment variables from .env file ---
load_dotenv()

# --- Configuration ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

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
PHONE_REGEX = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,}"

# --- CSV Field Names ---
CSV_FIELDS = ['Domain', 'Emails', 'Phone Numbers', 'Instagram', 'LinkedIn', 'X', 'Other Socials']

# --- Flask App Setup ---
app = Flask(__name__)

# Helper function to categorize social links
def categorize_social_link(url):
    try:
        # Check if URL is valid
        if not url or not isinstance(url, str):
            return "other", ""
            
        # Handle URLs that might not have protocol
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = 'https://' + url
                
        url_obj = urlparse(url)
        hostname = url_obj.netloc.lower().replace('www.', '')
        
        # Skip if hostname is empty
        if not hostname:
            return "other", url
            
        for domain, category in SOCIAL_MEDIA_DOMAINS.items():
            if hostname == domain or hostname.endswith('.' + domain):
                return category, url
        
        return "other", url
    except Exception as e:
        print(f"Error categorizing social link {url}: {e}")
        return "other", url

# Helper function to scrape a single domain
def scrape_domain(domain):
    try:
        # Clean domain name and ensure protocol prefix
        domain = domain.strip()
        # Handle potential entries that might be URLs or just domain names
        if not domain:
            return {
                'domain': "empty_entry",
                'emails': [],
                'phones': [],
                'instagram': "",
                'linkedin': "",
                'x': "",
                'other': []
            }
            
        # Store original domain for reporting
        original_domain = domain
        
        # Ensure domain has protocol prefix
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        print(f"\n--- Processing Domain: {domain} ---")
        
        driver = None
        social_links = {}
        emails_found = set()
        phones_found = set()
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)  # Timeout for initial page load
            
            print(f"Attempting to load URL: {domain}")
            driver.get(domain)
            
            # Wait for the page to load important elements
            try:
                # Try waiting for body element first, as a baseline
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Then try waiting for common elements in website footers (where contact info often appears)
                selectors = [
                    "a[href*='mailto']",  # Email links
                    "a[href*='tel']",     # Phone links
                    "footer",             # Footer element
                    ".footer",            # Common footer class
                    ".contact",           # Common contact class
                    "a[href*='instagram.com']", # Instagram links
                    "a[href*='linkedin.com']",  # LinkedIn links
                    "a[href*='twitter.com']",   # Twitter/X links
                    "a[href*='x.com']"          # X/Twitter links
                ]
                
                # Wait for at least one of these selectors (if any exists)
                for selector in selectors:
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"Found element matching: {selector}")
                        break  # Found one, no need to wait for others
                    except TimeoutException:
                        continue  # Try next selector
                        
            except TimeoutException:
                print(f"Could not find expected elements, but continuing with available content")
            
            # Get page source
            page_source = driver.page_source
            if not page_source:
                print(f"Warning: Empty page source for {domain}")
                return {
                    'domain': domain,
                    'emails': [],
                    'phones': [],
                    'instagram': "",
                    'linkedin': "",
                    'x': "",
                    'other': []
                }
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 1. Extract from Links
            links = soup.find_all('a', href=True)
            print(f"Found {len(links)} anchor tags for parsing")
            
            for link in links:
                href = link.get('href')
                if not href or not isinstance(href, str):
                    continue
                href = href.strip()
                if not href:
                    continue
                
                # Check for mailto links
                if href.startswith('mailto:'):
                    try:
                        email_part = href.split('mailto:', 1)[1].split('?')[0]
                        if email_part:
                            potential_email = unquote(email_part)
                            if re.fullmatch(EMAIL_REGEX, potential_email):
                                emails_found.add(potential_email)
                    except Exception as e:
                        print(f"Error processing mailto link '{href}': {e}")
                    continue
                
                # Check for tel links
                if href.startswith('tel:'):
                    try:
                        phone_part = href.split('tel:', 1)[1]
                        cleaned_phone = phone_part.strip()
                        if cleaned_phone:
                            phones_found.add(cleaned_phone)
                    except Exception as e:
                        print(f"Error processing tel link '{href}': {e}")
                    continue
                
                # Check for social media links
                try:
                    # Make sure the link is absolute
                    if not href.startswith(('http://', 'https://')):
                        if href.startswith('/'):
                            base_url = f"{urlparse(domain).scheme}://{urlparse(domain).netloc}"
                            href = f"{base_url}{href}"
                        else:
                            continue  # Skip relative links that aren't starting with /
                    
                    social_type, social_url = categorize_social_link(href)
                    if social_type != "other":
                        social_links.setdefault(social_type, social_url)
                    
                except Exception as e:
                    pass
            
            # 2. Extract from Page Text using Regex
            if soup.body:
                page_text = soup.body.get_text(separator=' ', strip=True)
                
                # Find emails in text
                try:
                    found_emails_in_text = re.findall(EMAIL_REGEX, page_text)
                    if found_emails_in_text:
                        emails_found.update(found_emails_in_text)
                except Exception as e:
                    print(f"Error finding emails: {e}")
                
                # Find phone numbers in text
                try:
                    found_phones_in_text = re.findall(PHONE_REGEX, page_text)
                    if found_phones_in_text:
                        processed_phones = []
                        for p in found_phones_in_text:
                            phone_str = "".join(filter(None, p)) if isinstance(p, tuple) else p
                            if phone_str:
                                processed_phones.append(phone_str.strip())
                        phones_found.update(processed_phones)
                except Exception as e:
                    print(f"Error finding phones: {e}")
            
            # Organize results
            other_socials = []
            for social_type, url in social_links.items():
                if social_type not in ['instagram', 'linkedin', 'x']:
                    other_socials.append(url)
            
            # Clean domain for display
            clean_domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
            
            result = {
                'domain': clean_domain,
                'emails': sorted(list(emails_found)),
                'phones': sorted(list(phones_found)),
                'instagram': social_links.get('instagram', ''),
                'linkedin': social_links.get('linkedin', ''),
                'x': social_links.get('x', ''),
                'other': other_socials
            }
            
            print(f"Extraction complete for {domain}")
            print(f"Found {len(emails_found)} emails, {len(phones_found)} phones, {len(social_links)} social links")
            
            return result
            
        except Exception as e:
            print(f"Error processing {domain}: {e}")
            return {
                'domain': domain.replace('https://', '').replace('http://', '').rstrip('/'),
                'emails': [],
                'phones': [],
                'instagram': "",
                'linkedin': "",
                'x': "",
                'other': []
            }
        finally:
            if driver:
                driver.quit()
                
    except Exception as e:
        print(f"Unexpected error for {domain}: {e}")
        return {
            'domain': domain,
            'emails': [],
            'phones': [],
            'instagram': "",
            'linkedin': "",
            'x': "",
            'other': []
        }

# --- API Endpoint to fetch domains from worker ---
@app.route('/process-domains', methods=['POST'])
def process_domains():
    # --- Authentication ---
    api_key = request.headers.get('api-key')
    expected_key = os.environ.get("MY_API_SECRET")
    if not expected_key:
        print("ERROR: MY_API_SECRET environment variable not found.")
        return jsonify({"error": "Server configuration error"}), 500
    if not api_key or api_key != expected_key:
        print(f"Unauthorized attempt.")
        return jsonify({"error": "Unauthorized"}), 401
    
    # --- Get Worker URL from Request Body ---
    data = request.get_json()
    if not data or 'worker_url' not in data:
        return jsonify({"error": "Missing 'worker_url' in request body"}), 400
    
    worker_url = data['worker_url']
    # Clean up target URL - remove duplicate gid parameters
    target_url = data.get('target_url', "https://docs.google.com/spreadsheets/d/11TyrFYEP99exnbfbgqKdh93yUaP3_NS1_LWEPy_cYh4/edit#gid=216454876")
    if "#gid=" in target_url and "?gid=" in target_url:
        # Keep only one gid parameter
        parts = target_url.split("#gid=")
        if len(parts) > 1:
            target_url = parts[0]
            if "?" not in target_url:
                target_url += "?"
            if not target_url.endswith("?"):
                target_url += "&"
            target_url += f"gid={parts[1]}"
    
    max_workers = data.get('max_workers', 5)  # Default to 5 concurrent workers
    
    print(f"\n--- New Domain Processing Request ---")
    print(f"Worker URL: {worker_url}")
    print(f"Target URL: {target_url}")
    
    try:
        # Call the worker to get domains
        print(f"Sending request to worker with data: {{'url': '{target_url}'}}")
        response = requests.post(worker_url, json={"url": target_url})
        
        print(f"Worker response status: {response.status_code}")
        if response.status_code != 200:
            error_text = response.text
            print(f"Worker error response: {error_text}")
            return jsonify({"error": f"Worker returned status code {response.status_code}: {error_text[:200]}"}), 500
        
        # Print response for debugging
        print(f"Worker response: {response.text[:200]}...")
        
        try:
            worker_data = response.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from worker response: {e}")
            print(f"Response content: {response.text[:500]}")
            return jsonify({"error": "Could not parse JSON response from worker"}), 500
        
        if not worker_data.get('success'):
            print(f"Worker returned unsuccessful status: {worker_data}")
            return jsonify({"error": f"Worker returned unsuccessful status: {worker_data}"}), 500
        
        domains = worker_data.get('domains', [])
        if not domains:
            print(f"No domains found in worker response: {worker_data}")
            return jsonify({"error": "No domains returned from worker"}), 400
        
        print(f"Received {len(domains)} domains from worker")
        
        # Process domains in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {executor.submit(scrape_domain, domain): domain for domain in domains}
            for future in future_to_domain:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    domain = future_to_domain[future]
                    print(f"Exception processing domain {domain}: {e}")
                    results.append({
                        'domain': domain,
                        'emails': [],
                        'phones': [],
                        'instagram': "",
                        'linkedin': "",
                        'x': "",
                        'other': []
                    })
        
        # Generate CSV file
        csv_filename = f"domain_contacts_{int(time.time())}.csv"
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(CSV_FIELDS)
                
                for result in results:
                    # Ensure all values are properly converted to strings
                    domain = str(result.get('domain', ''))
                    emails = [str(e) for e in result.get('emails', [])]
                    phones = [str(p) for p in result.get('phones', [])]
                    instagram = str(result.get('instagram', ''))
                    linkedin = str(result.get('linkedin', ''))
                    x_value = str(result.get('x', ''))
                    other = [str(o) for o in result.get('other', [])]
                    
                    writer.writerow([
                        domain,
                        '; '.join(emails),
                        '; '.join(phones),
                        instagram,
                        linkedin,
                        x_value,
                        '; '.join(other)
                    ])
            print(f"Successfully wrote CSV file with {len(results)} rows")
        except Exception as csv_err:
            print(f"Error writing CSV file: {csv_err}")
            # Continue execution - we'll return the data in JSON even if CSV fails
        
        print(f"CSV file generated: {csv_filename}")
        
        # Return the results
        return jsonify({
            "success": True,
            "message": f"Processed {len(results)} domains",
            "csv_filename": csv_filename,
            "results": results
        }), 200
        
    except Exception as e:
        print(f"Error in process-domains:")
        traceback.print_exc()
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# --- API Endpoint to download CSV file ---
@app.route('/download-csv/<filename>', methods=['GET'])
def download_csv(filename):
    # --- Authentication ---
    api_key = request.headers.get('api-key')
    expected_key = os.environ.get("MY_API_SECRET")
    if not expected_key:
        return jsonify({"error": "Server configuration error"}), 500
    if not api_key or api_key != expected_key:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        return send_file(filename, 
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=filename)
    except Exception as e:
        return jsonify({"error": f"Error downloading CSV file: {str(e)}"}), 500

# --- Single domain processing endpoint (original functionality) ---
@app.route('/extract-info', methods=['POST'])
def extract_info():
    # --- Authentication ---
    api_key = request.headers.get('api-key')
    expected_key = os.environ.get("MY_API_SECRET")
    if not expected_key:
        print("ERROR: MY_API_SECRET environment variable not found.")
        return jsonify({"error": "Server configuration error"}), 500
    if not api_key or api_key != expected_key:
        print(f"Unauthorized attempt.")
        return jsonify({"error": "Unauthorized"}), 401

    # --- Get URL from Request Body ---
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    target_url = data['url']
    
    # Use the scrape_domain function to process the single domain
    result = scrape_domain(target_url)
    
    # Return formatted results
    return jsonify({
        "social_links": result.get('instagram', '') + result.get('linkedin', '') + result.get('x', '') + result.get('other', []),
        "emails": result.get('emails', []),
        "phone_numbers": result.get('phones', [])
    }), 200

# --- Run the Flask App ---
if __name__ == '__main__':
    # Set debug=False when deploying to production
    app.run(host='0.0.0.0', port=5000, debug=True)
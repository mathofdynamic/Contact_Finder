#!/usr/bin/env python3
"""
Contact Finder Web Interface
============================

Professional web interface for batch processing company contact extraction.
Features:
- CSV file upload with company domains/names
- Real-time progress tracking with WebSocket
- Live results table updates
- Pause/Resume functionality
- Progress persistence
- Professional UI/UX with animations

Author: Contact Finder Team
"""

import os
import csv
import json
import time
import uuid
import signal
import threading
import queue
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Import our existing contact finder functionality
from company_contact_finder import CompanyContactFinder

# Load environment variables
load_dotenv()

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'contact-finder-secret-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROGRESS_FOLDER'] = 'progress_files'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables for managing processing sessions
processing_sessions = {}
session_lock = threading.Lock()

class ProcessingSession:
    def __init__(self, session_id, company_list, user_file_name):
        self.session_id = session_id
        self.company_list = company_list
        self.user_file_name = user_file_name
        self.total_companies = len(company_list)
        self.processed_companies = 0
        self.current_company = None
        self.is_running = False
        self.is_paused = False
        self.results = []
        self.errors = []
        self.start_time = time.time()
        self.progress_file_path = os.path.join(app.config['PROGRESS_FOLDER'], f'progress_{session_id}.json')
        self.results_file_path = os.path.join(app.config['RESULTS_FOLDER'], f'results_{session_id}.csv')
        # Don't create contact_finder here - create fresh instances per company to avoid threading issues
        
    def save_progress(self):
        """Save current progress to file for persistence"""
        progress_data = {
            'session_id': self.session_id,
            'user_file_name': self.user_file_name,
            'total_companies': self.total_companies,
            'processed_companies': self.processed_companies,
            'current_company': self.current_company,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'start_time': self.start_time,
            'company_list': self.company_list,
            'results': self.results,
            'errors': self.errors
        }
        
        with open(self.progress_file_path, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def load_progress(self):
        """Load progress from file if exists"""
        if os.path.exists(self.progress_file_path):
            try:
                with open(self.progress_file_path, 'r') as f:
                    progress_data = json.load(f)
                
                self.processed_companies = progress_data.get('processed_companies', 0)
                self.current_company = progress_data.get('current_company')
                self.start_time = progress_data.get('start_time', time.time())
                self.results = progress_data.get('results', [])
                self.errors = progress_data.get('errors', [])
                return True
            except Exception as e:
                print(f"Error loading progress: {e}")
        return False
    
    def get_progress_percentage(self):
        """Calculate current progress percentage"""
        if self.total_companies == 0:
            return 0
        return round((self.processed_companies / self.total_companies) * 100, 1)
    
    def get_remaining_companies(self):
        """Get list of remaining companies to process"""
        return self.company_list[self.processed_companies:]
    
    def export_to_csv(self):
        """Export current results to CSV file"""
        if not self.results:
            return False
        
        try:
            # Define CSV headers
            headers = [
                'Company Domain',
                'Company Name', 
                'Website Emails',
                'Website Phones',
                'Website Social Links',
                'CEO LinkedIn',
                'CEO Twitter/X',
                'CEO Instagram',
                'CEO TikTok',
                'CEO Email',
                'Email Confidence',
                'Search Method',
                'Search Confidence',
                'Processing Status',
                'Timestamp'
            ]
            
            with open(self.results_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                for result in self.results:
                    # Extract data from result
                    company_data = result.get('company_website_data', {})
                    ceo_data = result.get('ceo_data', {})
                    
                    # Extract CEO profiles with proper handling for Twitter/X
                    ceo_profiles = ceo_data.get('ceo_profiles', {})
                    linkedin_url = ''
                    twitter_url = ''
                    instagram_url = ''
                    tiktok_url = ''
                    
                    # Extract URLs from ceo_profiles
                    for platform, profile_data in ceo_profiles.items():
                        if isinstance(profile_data, dict) and profile_data.get('url'):
                            if 'linkedin' in platform:
                                linkedin_url = profile_data['url']
                            elif 'twitter' in platform or 'x' in platform:
                                if not twitter_url:  # Only take the first Twitter/X URL found
                                    twitter_url = profile_data['url']
                            elif 'instagram' in platform:
                                instagram_url = profile_data['url']
                            elif 'tiktok' in platform:
                                tiktok_url = profile_data['url']
                    
                    # Fallback to direct keys if profiles not found
                    if not linkedin_url:
                        linkedin_url = ceo_data.get('linkedin', '')
                    if not twitter_url:
                        twitter_url = ceo_data.get('twitter', '') or ceo_data.get('x', '')
                    if not instagram_url:
                        instagram_url = ceo_data.get('instagram', '')
                    if not tiktok_url:
                        tiktok_url = ceo_data.get('tiktok', '')
                    
                    row = [
                        result.get('company_domain', ''),
                        result.get('company_name', ''),
                        '; '.join(company_data.get('emails', [])),
                        '; '.join(company_data.get('phones', [])),
                        self._format_social_links(company_data.get('socialLinks', {})),
                        linkedin_url,
                        twitter_url,
                        instagram_url,
                        tiktok_url,
                        ceo_data.get('ceo_email', ''),
                        f"{ceo_data.get('email_confidence', 0)}%" if ceo_data.get('email_confidence', 0) > 0 else '',
                        ceo_data.get('search_method', 'Unknown'),
                        ceo_data.get('search_confidence', 'Unknown'),
                        'Success' if result.get('success') else 'Failed',
                        datetime.fromtimestamp(result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def _format_social_links(self, social_links):
        """Format social links dictionary into readable string"""
        if not social_links:
            return ''
        
        formatted_links = []
        for platform, url in social_links.items():
            if url:
                formatted_links.append(f"{platform.title()}: {url}")
        
        return '; '.join(formatted_links)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

def parse_company_file(file_path, filename):
    """Parse uploaded file to extract company domains/names"""
    companies = []
    
    try:
        print(f"📄 Parsing file: {filename} at {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"📊 File size: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        print(f"📋 File extension: {file_ext}")
        
        if file_ext == 'csv':
            # Try different encodings for CSV
            encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    print(f"🔤 Trying encoding: {encoding}")
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"✅ Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError as e:
                    print(f"❌ {encoding} failed: {e}")
                    continue
                except Exception as e:
                    print(f"❌ {encoding} failed with error: {e}")
                    continue
            
            if df is None:
                raise ValueError("Could not read CSV file with any supported encoding")
                
        elif file_ext in ['xlsx', 'xls']:
            print(f"📊 Reading Excel file...")
            df = pd.read_excel(file_path)
            print(f"✅ Successfully read Excel file")
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        print(f"📈 DataFrame shape: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Look for company domain/name columns
        possible_columns = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['company', 'domain', 'website', 'url', 'site']):
                possible_columns.append(col)
        
        # If no obvious column found, use the first column
        if not possible_columns:
            possible_columns = [df.columns[0]]
        
        target_column = possible_columns[0]
        print(f"🎯 Using column: '{target_column}'")
        
        # Extract companies from the first matching column
        for index, row in df.iterrows():
            try:
                company_value = str(row[target_column]).strip()
                if company_value and company_value.lower() not in ['nan', 'none', '', 'null']:
                    companies.append(company_value)
            except Exception as e:
                print(f"⚠️ Error processing row {index}: {e}")
                continue
        
        print(f"🏢 Found {len(companies)} companies")
        if companies:
            print(f"📋 First 3 companies: {companies[:3]}")
        
        return companies, target_column
        
    except Exception as e:
        error_msg = f"Error parsing file {filename}: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        raise e

@app.route('/')
def index():
    """Main page of the web interface"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing session"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Please upload CSV, XLSX, or XLS files only.'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        if not file.filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid or unsafe filename'}), 400
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        # Parse company list from file
        companies, detected_column = parse_company_file(file_path, filename)
        
        if not companies:
            return jsonify({'error': 'No companies found in the uploaded file'}), 400
        
        # Create processing session
        session = ProcessingSession(session_id, companies, filename)
        
        with session_lock:
            processing_sessions[session_id] = session
        
        # Try to load existing progress
        session.load_progress()
        session.save_progress()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_companies': len(companies),
            'detected_column': detected_column,
            'companies_preview': companies[:5],  # Preview first 5 companies
            'progress_percentage': session.get_progress_percentage()
        })
        
    except Exception as e:
        print(f"Error in upload_file: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

def process_single_company_isolated(company, session_id):
    """Process a single company in complete thread isolation from Flask-SocketIO"""
    try:
        # Create a completely fresh contact finder instance in this thread
        # This ensures no shared state with Flask-SocketIO's asyncio loop
        contact_finder = CompanyContactFinder(skip_ceo_on_captcha=False)
        
        print(f"\n🎯 Processing: {company}")
        print("=" * 60)
        
        # Process the company (this will create its own browser instance)
        result = contact_finder.find_company_contacts(company)
        
        # Clean up the browser after processing this company
        contact_finder.cleanup_browser()
        
        return {
            'success': True,
            'company': company,
            'result': result,
            'error': None
        }
        
    except Exception as e:
        print(f"❌ Error processing {company}: {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        
        return {
            'success': False,
            'company': company,
            'result': None,
            'error': str(e)
        }

def process_companies_background(session_id):
    """Background function to process companies with real-time updates"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            print(f"Session {session_id} not found")
            return
        
        session.is_running = True
        session.is_paused = False
        session.save_progress()
        
        # Get remaining companies to process
        remaining_companies = session.get_remaining_companies()
        
        for i, company in enumerate(remaining_companies):
            # Check if processing should be paused
            if session.is_paused:
                session.is_running = False
                session.save_progress()
                socketio.emit('processing_paused', {
                    'session_id': session_id,
                    'message': 'Processing paused by user'
                })
                break
            
            try:
                session.current_company = company
                session.save_progress()
                
                # Emit progress update
                socketio.emit('progress_update', {
                    'session_id': session_id,
                    'current_company': company,
                    'processed': session.processed_companies,
                    'total': session.total_companies,
                    'percentage': session.get_progress_percentage()
                })
                
                # Emit log message
                socketio.emit('log_message', {
                    'session_id': session_id,
                    'message': f"🔄 Processing: {company}",
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'type': 'info'
                })
                
                # Process the company using thread isolation to avoid asyncio conflicts
                result_queue = queue.Queue()
                
                def isolated_worker():
                    """Worker function that runs in complete isolation"""
                    result = process_single_company_isolated(company, session_id)
                    result_queue.put(result)
                
                # Create and start isolated thread
                worker_thread = threading.Thread(target=isolated_worker)
                worker_thread.start()
                
                # Wait for result (this is safe in background thread)
                worker_thread.join()
                processing_result = result_queue.get()
                
                if processing_result['success']:
                    result = processing_result['result']
                    session.results.append(result)
                    
                    # Emit detailed result for table display
                    ceo_profiles = result.get('ceo_data', {}).get('ceo_profiles', {})
                    ceo_count = len([p for p in ceo_profiles.values() if p.get('url')])
                    
                    # Extract CEO profile URLs for display
                    linkedin_url = ""
                    twitter_url = ""
                    instagram_url = ""
                    tiktok_url = ""
                    
                    for platform, profile_data in ceo_profiles.items():
                        if profile_data.get('url'):
                            if 'linkedin' in platform:
                                linkedin_url = profile_data['url']
                            elif 'twitter' in platform or 'x' in platform:
                                twitter_url = profile_data['url']
                            elif 'instagram' in platform:
                                instagram_url = profile_data['url']
                            elif 'tiktok' in platform:
                                tiktok_url = profile_data['url']
                    
                    # Extract website data for display
                    website_data = result.get('company_website_data', {})
                    emails = website_data.get('emails', [])
                    phones = website_data.get('phones', [])
                    social_links = website_data.get('social_links', {})
                    
                    socketio.emit('result_update', {
                        'session_id': session_id,
                        'company': company,
                        'result': result,
                        'status': 'success',
                        'detailed_info': {
                            'ceo_profiles_count': ceo_count,
                            'linkedin_url': linkedin_url,
                            'twitter_url': twitter_url,
                            'instagram_url': instagram_url,
                            'tiktok_url': tiktok_url,
                            'ceo_email': result.get('ceo_data', {}).get('ceo_email', ''),
                            'email_confidence': result.get('ceo_data', {}).get('email_confidence', 0),
                            'emails_found': emails,
                            'phones_found': phones,
                            'social_links_found': list(social_links.keys()) if social_links else [],
                            'search_method': result.get('ceo_data', {}).get('search_method', 'unknown'),
                            'search_confidence': result.get('ceo_data', {}).get('search_confidence', 'unknown')
                        }
                    })
                    
                    socketio.emit('log_message', {
                        'session_id': session_id,
                        'message': f"✅ Completed: {company}",
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'type': 'success'
                    })
                else:
                    # Handle error case
                    error_msg = processing_result['error']
                    session.errors.append({
                        'company': company,
                        'errors': [error_msg],
                        'timestamp': time.time()
                    })
                    
                    socketio.emit('result_update', {
                        'session_id': session_id,
                        'company': company,
                        'result': {'error': error_msg},
                        'status': 'error'
                    })
                    
                    socketio.emit('log_message', {
                        'session_id': session_id,
                        'message': f"❌ Failed: {company} - {error_msg}",
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'type': 'error'
                    })
                
                session.processed_companies += 1
                session.save_progress()
                
                # Export results to CSV after each successful processing
                session.export_to_csv()
                
                # Add delay between requests to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"Exception processing {company}: {str(e)}"
                print(error_msg)
                
                session.errors.append({
                    'company': company,
                    'errors': [error_msg],
                    'timestamp': time.time()
                })
                
                socketio.emit('log_message', {
                    'session_id': session_id,
                    'message': f"❌ Error: {company} - {error_msg}",
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'type': 'error'
                })
                
                session.processed_companies += 1
                session.save_progress()
        
        # Processing completed
        if not session.is_paused:
            session.is_running = False
            session.current_company = None
            
            # Clean up any remaining resources since processing is complete
            # (Each company already cleaned up its own browser instance)
            print(f"Session {session_id} processing completed")
            
            session.save_progress()
            
            # Final CSV export
            session.export_to_csv()
            
            # Send final progress update to ensure 100% completion
            socketio.emit('progress_update', {
                'session_id': session_id,
                'current_company': 'Processing Complete!',
                'processed': session.total_companies,
                'total': session.total_companies,
                'percentage': 100
            })
            
            socketio.emit('processing_complete', {
                'session_id': session_id,
                'total_processed': session.processed_companies,
                'total_companies': session.total_companies,
                'success_count': len(session.results),
                'error_count': len(session.errors),
                'csv_available': os.path.exists(session.results_file_path)
            })
            
            socketio.emit('log_message', {
                'session_id': session_id,
                'message': f"🎉 Processing completed! {len(session.results)} successful, {len(session.errors)} errors",
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'type': 'success'
            })
    
    except Exception as e:
        print(f"Error in background processing: {e}")
        socketio.emit('log_message', {
            'session_id': session_id,
            'message': f"💥 Critical error in processing: {str(e)}",
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'type': 'error'
        })

@app.route('/start_processing/<session_id>', methods=['POST'])
def start_processing(session_id):
    """Start or resume processing for a session"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.is_running:
            return jsonify({'error': 'Processing is already running'}), 400
        
        # Start background processing
        thread = threading.Thread(target=process_companies_background, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        # Emit initial log message about captcha handling
        socketio.emit('log_message', {
            'session_id': session_id,
            'message': '🔍 Browser runs headless by default - will show only if captcha is detected',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'type': 'info'
        })
        
        return jsonify({'success': True, 'message': 'Processing started'})
        
    except Exception as e:
        return jsonify({'error': f'Error starting processing: {str(e)}'}), 500

@app.route('/pause_processing/<session_id>', methods=['POST'])
def pause_processing(session_id):
    """Pause processing for a session"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.is_paused = True
        session.save_progress()
        
        # Optionally clean up browser when paused (user can choose to keep or clean)
        # For now, keep browser open for easier resuming
        
        return jsonify({'success': True, 'message': 'Processing will pause after current company'})
        
    except Exception as e:
        return jsonify({'error': f'Error pausing processing: {str(e)}'}), 500

@app.route('/stop_processing/<session_id>', methods=['POST'])
def stop_processing(session_id):
    """Stop and cleanup processing for a session"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.is_paused = True
        session.is_running = False
        
        # Note: Each company creates its own browser instance and cleans up automatically
        print(f"Processing stopped for session {session_id}")
        
        session.save_progress()
        
        return jsonify({'success': True, 'message': 'Processing stopped and browser cleaned up'})
        
    except Exception as e:
        return jsonify({'error': f'Error stopping processing: {str(e)}'}), 500

@app.route('/session_status/<session_id>')
def session_status(session_id):
    """Get current status of a processing session"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'total_companies': session.total_companies,
            'processed_companies': session.processed_companies,
            'current_company': session.current_company,
            'is_running': session.is_running,
            'is_paused': session.is_paused,
            'progress_percentage': session.get_progress_percentage(),
            'success_count': len(session.results),
            'error_count': len(session.errors),
            'csv_available': os.path.exists(session.results_file_path)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting session status: {str(e)}'}), 500

@app.route('/company_details/<session_id>/<path:company_domain>')
def get_company_details(session_id, company_domain):
    """Get detailed information for a specific company by domain"""
    try:
        # Decode URL-encoded domain
        from urllib.parse import unquote
        company_domain = unquote(company_domain)
        
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Find the company result by domain (more reliable than name)
        company_result = None
        print(f"Debug: Looking for company with domain containing: '{company_domain}'")
        
        # Clean the search domain for better matching
        search_domain = company_domain.replace('https://', '').replace('http://', '').replace('www.', '').lower()
        
        for i, result in enumerate(session.results):
            result_domain = result.get('company_domain', '')
            result_name = result.get('company_name', '')
            
            # Clean the result domain for comparison
            clean_result_domain = result_domain.replace('https://', '').replace('http://', '').replace('www.', '').lower()
            
            print(f"Debug: Checking result {i}: domain='{result_domain}', clean_domain='{clean_result_domain}', name='{result_name}'")
            
            # Handle different domain formats - be more flexible
            domain_matches = (
                search_domain in clean_result_domain or 
                clean_result_domain in search_domain or
                search_domain == clean_result_domain or
                company_domain.lower() in result_domain.lower() or
                result_domain.lower().endswith(search_domain)
            )
            
            if domain_matches:
                company_result = result
                print(f"Debug: Found matching company: {result_name}")
                break
        
        if not company_result:
            # Fallback: try to match by company name if domain matching failed
            print(f"Debug: Domain matching failed, trying to match by name: '{company_domain}'")
            for i, result in enumerate(session.results):
                result_name = result.get('company_name', '').lower()
                if company_domain.lower() in result_name or result_name in company_domain.lower():
                    company_result = result
                    print(f"Debug: Found matching company by name: {result.get('company_name')}")
                    break
        
        if not company_result:
            # Debug: List available companies for troubleshooting
            available_companies = [f"{r.get('company_name', 'N/A')} ({r.get('company_domain', 'N/A')})" for r in session.results]
            print(f"Debug: Company '{company_domain}' not found. Available companies: {available_companies}")
            return jsonify({
                'error': f'Company not found for domain: {company_domain}',
                'available_companies': available_companies
            }), 404
        
        # Format detailed response
        company_data = company_result.get('company_website_data', {})
        ceo_data = company_result.get('ceo_data', {})
        ceo_profiles = ceo_data.get('ceo_profiles', {})
        
        # Collect all found links
        all_links = {
            'emails': company_data.get('emails', []),
            'phones': company_data.get('phones', []),
            'website_social_links': company_data.get('socialLinks', {}),
            'ceo_profiles': {}
        }
        
        # Process CEO profiles
        for platform, profile_data in ceo_profiles.items():
            if isinstance(profile_data, dict) and profile_data.get('url'):
                all_links['ceo_profiles'][platform] = {
                    'url': profile_data['url'],
                    'name': profile_data.get('name', 'CEO Profile'),
                    'headline': profile_data.get('headline', 'Profile found via Google search')
                }
        
        return jsonify({
            'success': True,
            'company_name': company_result.get('company_name', ''),
            'company_domain': company_result.get('company_domain', ''),
            'timestamp': datetime.fromtimestamp(company_result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
            'processing_status': 'Success' if company_result.get('success') else 'Failed',
            'details': all_links,
            'ceo_email': ceo_data.get('ceo_email', ''),
            'email_confidence': ceo_data.get('email_confidence', 0),
            'errors': company_result.get('errors', [])
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting company details: {str(e)}'}), 500

@app.route('/download_results/<session_id>')
def download_results(session_id):
    """Download CSV results for a session"""
    try:
        with session_lock:
            session = processing_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if not os.path.exists(session.results_file_path):
            return jsonify({'error': 'Results file not found'}), 404
        
        return send_file(
            session.results_file_path,
            as_attachment=True,
            download_name=f'contact_finder_results_{session_id}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error downloading results: {str(e)}'}), 500

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    if session_id:
        print(f'Client joined session: {session_id}')

def cleanup_all_sessions():
    """Clean up browser resources for all active sessions"""
    print("🧹 Cleaning up all browser sessions...")
    with session_lock:
        for session_id, session in processing_sessions.items():
            try:
                if hasattr(session, 'contact_finder'):
                    session.contact_finder.cleanup_browser()
                    print(f"   ✅ Cleaned session {session_id}")
            except Exception as e:
                print(f"   ❌ Error cleaning session {session_id}: {e}")
    print("🏁 All sessions cleaned up")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutdown signal received, cleaning up...")
    cleanup_all_sessions()
    exit(0)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create necessary directories
    for folder in ['uploads', 'progress_files', 'results']:
        os.makedirs(folder, exist_ok=True)
    
    print("🚀 Starting Contact Finder Web Interface...")
    print("📂 Upload folder:", app.config['UPLOAD_FOLDER'])
    print("📊 Progress folder:", app.config['PROGRESS_FOLDER'])
    print("📁 Results folder:", app.config['RESULTS_FOLDER'])
    print("🔍 Browser will be persistent across companies (more efficient)")
    print("👀 Browser will be visible for manual captcha solving")
    
    try:
        # Run with SocketIO
        socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received, cleaning up...")
        cleanup_all_sessions()
    except Exception as e:
        print(f"\n❌ Error running web interface: {e}")
        cleanup_all_sessions()
    finally:
        cleanup_all_sessions()
# Contact Finder - Professional Contact & CEO Discovery Tool

<div align="center">
  <img src="https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Main_Page_contact_finder.jpg" alt="Contact Finder Web Interface" width="800"/>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
  [![Playwright](https://img.shields.io/badge/playwright-enabled-green.svg)](https://playwright.dev/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

## 🚀 Overview

Contact Finder is a comprehensive web application that automatically discovers and extracts contact information from companies, including:

### 🎯 What it extracts:
- 📧 **Website contact emails** (support, sales, info, etc.)
- 📞 **Phone numbers** with validation
- 🔗 **Social media profiles** (Instagram, LinkedIn, X/Twitter, Facebook, TikTok)
- 👤 **CEO LinkedIn profiles** with automated discovery
- 🐦 **CEO Twitter/X accounts** through intelligent search
- 📸 **CEO Instagram profiles** for comprehensive outreach
- 🎵 **CEO TikTok accounts** for modern social presence

### 🌟 Key Features:
- **Professional Web Interface** with real-time processing
- **Drag & Drop CSV Upload** supporting up to 16MB files
- **Live Progress Tracking** with WebSocket updates
- **CEO Profile Discovery** using advanced Google search automation
- **Pause/Resume Functionality** for large batch processing
- **Smart Captcha Handling** with automatic browser visibility
- **Comprehensive CSV Export** with all discovered data
- **Mobile-Responsive Design** for processing on any device

---

## 🎥 Live Demo - Web Interface in Action

### 📁 Input CSV File Format
<div align="center">
  <img src="https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/input_csv_file_example.png" alt="Input CSV File Example" width="600"/>
  <p><em>Simple CSV format: Just company domains, one per line</em></p>
</div>

### 📋 Professional Results Export
<div align="center">
  <img src="https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/finished_csv_file_example.png" alt="Finished CSV Results" width="800"/>
  <p><em>Comprehensive CSV export with all discovered contact information and CEO profiles</em></p>
</div>

### 🎆 Live Processing Demo
<div align="center">
  <img src="https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Screen_Recording_Company_contact_finder_working.gif" alt="Contact Finder Working" width="800"/>
  <p><em>Real-time processing with live progress updates, results table, and professional UI</em></p>
</div>

### 📊 Processing Results:
- **Processed**: monad.xyz, eigenlayer.xyz, celestia.org, ritual.net, berachain.com
- **Extracted**: 15+ email addresses across all companies
- **CEO Profiles Found**: 8 LinkedIn profiles, 6 Twitter accounts
- **Social Links**: Instagram, TikTok, and other social media presence
- **Phone Numbers**: Direct contact numbers where available
- **Processing Time**: ~2 minutes for 5 companies with full CEO discovery

---

## 📸 API Examples & Screenshots

### 1. Single Domain Request

**Request Example:**
```json
{
  "url": "https://droplinked.com/"
}
```
**Response Example:**
```json
{
  "csv_filename": "single_domain_1746616778.csv",
  "message": "Processed 1 domain. CSV generated.",
  "results": [
    {
      "domain": "droplinked.com",
      "logoURL": "https://droplinked.com/apple-touch-icon.png",
      "emails": ["support@droplinked.com"],
      "phones": [],
      "socialLinks": {
        "instagram": "https://www.instagram.com/drop_linked",
        "linkedin": "https://www.linkedin.com/company/droplinked",
        "x": "https://twitter.com/droplinked"
      }
    }
  ],
  "success": true
}
```
![Single Domain Request Screenshot](https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Contact_extractor_single_Request.png)
*Figure: Example of a single domain extraction request and response.*

---

### 2. Array Request

**Request Example:**
```json
{
  "domains": [
    "https://www.digikala.com/",
    "https://droplinked.com/",
    "https://flatlay.io/"
  ],
  "max_workers": 3,
  "generate_csv": false
}
```
**Response Example:**
```json
{
  "csv_filename": "array_domains_1746597667.csv",
  "message": "Processed 3 domains.",
  "results": [
    { "domain": "digikala.com", ... },
    { "domain": "droplinked.com", ... },
    { "domain": "flatlay.io", ... }
  ]
}
```
![Array Request Screenshot](https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Contact_extractor_Array.png?raw=true)
*Figure: Example of processing multiple domains in a single request.*

---

### 3. CSV Request

**Request Example:**
```json
{
  "csv_url": "https://storage3.fastupload.io/6e54370ba070c37a/test-_.Sheet1.csv?...",
  "max_workers": 5
}
```
**Response Example:**
```json
{
  "csv_filename": "csv_import_domains_1746616971.csv",
  "message": "Processed 20 domains. Extracted 20 domain(s) from CSV.",
  "results": [
    { "domain": "impactcanopy.com", ... },
    ...
  ]
}
```
![CSV Request Screenshot](https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Contact_extractor_CSV_request.png)
*Figure: Example of extracting contacts from a CSV file of domains.*

---

### 4. Sheet Request

**Request Example:**
```json
{
  "target_url": "https://docs.google.com/spreadsheets/d/...",
  "max_workers": 10
}
```
**Response Example:**
```json
{
  "csv_filename": "sheet_import_domains_1746616351.csv",
  "message": "Processed 20 domains. Received 20 domain(s) from sheet worker.",
  "results": [
    { "domain": "impactcanopy.com", ... },
    ...
  ]
}
```
![Sheet Request Screenshot](https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Contact_extractor_Sheet.png)
*Figure: Example of extracting contacts from a Google Sheet of domains.*

---

## ✨ Features

### 🌐 **Modern Web Interface** (Primary Method - Recommended)
- **📁 Smart File Upload**: Drag & drop CSV/XLSX/XLS files (up to 16MB)
- **🔄 Real-time Processing**: Live progress bar with animated glow effects
- **📋 Live Results Table**: See contacts appear as companies are processed
- **⏸️ Pause/Resume**: Stop and continue processing anytime
- **📋 Live Logs**: Color-coded processing messages in real-time
- **💾 Progress Persistence**: Resume interrupted sessions automatically
- **📊 Professional CSV Export**: Download comprehensive results anytime
- **🎨 Modern UI/UX**: Professional design with smooth animations
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **🔍 Smart Detection**: Automatically detects company domain/name columns
- **👁️ View Details**: Clickable company details with modal interface
- **🛡️ Security**: File validation, session isolation, secure uploads
- **⚡ Performance**: Background processing with thread isolation
- **📈 Analytics**: Real-time statistics and success/error tracking

### 🎯 **Advanced CEO Discovery**
- **🔍 Google Search Automation**: Uses Playwright for intelligent profile discovery
- **👤 LinkedIn Profile Extraction**: Finds CEO/founder LinkedIn profiles
- **🐦 Twitter/X Discovery**: Locates executive Twitter accounts
- **📸 Instagram & TikTok**: Discovers CEO social media presence
- **🤖 Smart Captcha Handling**: Browser becomes visible only when captcha detected
- **📊 Thread Isolation**: Prevents browser conflicts with asyncio
- **🔄 Anti-Detection**: Stealth mode with human-like behavior

### 🔍 **Intelligent Contact Detection**
- **📧 Advanced Email Patterns**: Recognizes all common email formats
- **📞 Smart Phone Validation**: Validates and formats phone numbers
- **🔗 Social Media Categorization**: Automatically categorizes social links
- **📝 Footer Analysis**: Focuses on contact-rich footer sections
- **🏢 Company Logo Detection**: Extracts company branding assets

### 🚀 **Multiple Processing Methods**
- **👑 Web Interface**: Primary method with full feature set
- **🔗 Single Domain API**: Process individual domains
- **📋 Array API**: Process multiple domains in parallel
- **📄 CSV API**: Batch process from CSV files
- **📊 Google Sheets API**: Direct integration with spreadsheets

### 🔒 **Security & Performance**
- **🔑 API Key Authentication**: Secure request handling
- **✅ Input Validation**: Comprehensive data validation
- **🛡️ File Security**: Upload validation and sanitization
- **🔄 Session Management**: Isolated processing sessions
- **📏 Rate Limiting**: Prevents abuse and overload

### 📊 **Output & Export Options**
- **📝 JSON Response**: Structured API responses
- **📊 Professional CSV**: Comprehensive data export
- **📈 Real-time Results**: Live data as it's discovered
- **💾 Session Persistence**: Never lose processing progress
- **🔗 Clickable Links**: Mailto and tel links in web interface

## 🛠️ Installation

### 🚀 Quick Start (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/contact-finder.git
cd contact-finder
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install all dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements_web.txt
```

4. **Install Playwright browsers (Essential for CEO discovery):**
```bash
playwright install
```

5. **Configure environment variables:**
Create a `.env` file with your configuration:
```env
# Required for API authentication
MY_API_SECRET=your_api_key_here

# Optional: Google Sheets integration
GOOGLE_SHEET_WORKER_URL=your_google_sheet_worker_url

# Required for CEO discovery (paths to cookie files)
GOOGLE_COOKIES_PATH="google-cookie.json"
LINKEDIN_COOKIES_PATH="linkedin_cookies.json"

# Optional: Proxy configuration for captcha bypass
# PROXY_URL="http://username:password@proxy.com:8080"

# Development mode (Optional - Default: False)
DEBUG=False

# Optional: Custom Chrome driver path
# DRIVER_PATH=path_to_chromedriver
```

### 🎆 **Ready to Launch!**

After installation, you can start using Contact Finder immediately:

```bash
# Start the modern web interface (Recommended)
python web_interface.py
# ➜ Open http://localhost:5001 in your browser

# OR start the API service
python Contact_extractor.py
# ➜ API available at http://localhost:5000
```

## 🚀 Usage

### 🌐 Web Interface (Primary Method - Recommended)

The modern web interface provides the most comprehensive and user-friendly experience:

```bash
# Start the web interface
python web_interface.py
```

**➜ Access at: `http://localhost:5001`**

#### 🎆 **Complete Workflow:**

1. **📁 Prepare Your Data**
   - Create a CSV file with company domains (see example above)
   - Supported formats: CSV, XLSX, XLS (up to 16MB)
   - Simple format: one column with company domains/names

2. **📎 Upload & Configure**
   - Drag & drop your file or click to browse
   - Preview detected companies and verify column selection
   - Review processing settings

3. **▶️ Start Processing**
   - Click "Start Processing" to begin contact discovery
   - Watch real-time progress with animated progress bar
   - Monitor live processing logs with color-coded messages

4. **👁️ Monitor Results**
   - See results appear in real-time as companies are processed
   - View detailed statistics: emails found, profiles discovered
   - Use pause/resume functionality for large batches

5. **📄 Export Results**
   - Download comprehensive CSV export anytime
   - Click "View Details" for individual company information
   - All contact information organized and validated

#### 📊 **What You'll Discover:**

**Per Company Website:**
- 📧 All email addresses (support, sales, info, contact, etc.)
- 📞 Phone numbers with international formatting
- 🔗 Social media links (Instagram, LinkedIn, Twitter, Facebook, TikTok)
- 🏢 Company logo URLs

**Per CEO/Executive:**
- 👤 LinkedIn profile URL with validation
- 🐦 Twitter/X profile with handle verification
- 📸 Instagram profile for visual content marketing
- 🎵 TikTok account for modern social presence

#### 🛅 **Advanced Features:**

**Smart Processing:**
- **Thread Isolation**: Each company processed in isolated thread
- **Browser Management**: Headless by default, visible during captchas
- **Auto-Resume**: Interrupted sessions automatically resume
- **Real-time Updates**: WebSocket communication for live updates

**Professional UI:**
- **Responsive Design**: Works on desktop, tablet, mobile
- **Live Animations**: Smooth progress indicators with glow effects
- **Modal Details**: Click any company for detailed contact view
- **Export Options**: Professional CSV with all discovered data

**Security & Performance:**
- **File Validation**: Secure upload with format verification
- **Session Management**: Isolated processing with unique IDs
- **Progress Persistence**: Never lose work due to interruptions
- **Memory Efficient**: Optimized for large company lists

#### 🔧 **Web Interface Configuration:**

**File Upload Settings:**
```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
```

**Processing Optimization:**
```python
# Adjust in company_contact_finder.py
PROCESSING_TIMEOUT = 30  # seconds per company
DELAY_BETWEEN_REQUESTS = 2  # seconds between requests
HEADLESS_BROWSER = True  # invisible unless captcha
```

**UI Customization:**
```css
/* Modify in static/css/main.css */
:root {
    --primary: #2563eb;
    --success: #059669;
    --warning: #d97706;
    --danger: #dc2626;
}
```

#### 🚨 **Troubleshooting:**

**Common Issues:**

1. **"WebSocket connection failed"**
   - Ensure port 5001 is available
   - Check firewall settings
   - Restart the application

2. **"Playwright browser not found"**
   - Run: `playwright install`
   - Verify internet connection
   - Check browser installation logs

3. **"File upload failed"**
   - Check file size (max 16MB)
   - Verify file format (CSV/XLSX/XLS)
   - Ensure file is not corrupted

4. **"No companies detected"**
   - Verify CSV format and encoding (UTF-8 recommended)
   - Check that first row contains domains/company names
   - Try different column if auto-detection fails

5. **"Browser captcha stuck"**
   - Browser will automatically become visible
   - Solve captcha manually in the visible browser
   - Processing resumes automatically after solving

**Performance Tips:**
- **Optimal batch size**: 10-50 companies per session
- **Stable internet**: Required for web scraping and Google searches
- **Close other browsers**: Reduces memory usage during processing
- **Regular saves**: Automatic progress saving prevents data loss

### 📏 **CSV Input Format:**

Simple and flexible - just company domains:

```csv
Company domains
monad.xyz
eigenlayer.xyz
celestia.org
ritual.net
berachain.com
starkware.co
polygon.technology
avax.network
```

**Alternative formats supported:**
```csv
Company Name,Website
Monad Labs,monad.xyz
EigenLayer,eigenlayer.xyz
Celestia,celestia.org
```

### 📊 **CSV Export Format:**

Comprehensive results with all discovered information:

| Column | Description | Example |
|--------|-------------|----------|
| Company Domain | Main website | monad.xyz |
| Company Name | Detected name | Monad Labs |
| Website Emails | All found emails | support@monad.xyz, hello@monad.xyz |
| Website Phones | Contact numbers | +1-555-0123 |
| Website Social Links | Social media | {"linkedin": "linkedin.com/company/monad"} |
| CEO LinkedIn | Executive profile | linkedin.com/in/keonehan |
| CEO Twitter/X | Twitter handle | twitter.com/keonehan |
| CEO Instagram | Instagram profile | instagram.com/keonehan |
| CEO TikTok | TikTok account | tiktok.com/@keonehan |
| Processing Status | Success/Error | Success |
| Timestamp | Processing time | 2024-01-15 14:30:25 |

---

### 🔗 API Service (Advanced Users)

```bash
# Start the API service
python Contact_extractor.py
```

**➜ API available at: `http://localhost:5000`**

#### 🔗 **API Quick Examples:**

---

### 🎯 **Standalone Lead Finding Tool**

For advanced users who want to use just the CEO discovery functionality:

```bash
python lead_finder.py
```

#### 🛠️ **Setup Requirements:**
1. **Google Cookies**: Export from browser and save as `google-cookie.json`
2. **LinkedIn Cookies**: Export using browser extension, save as `linkedin_cookies.json`
3. **Browser Installation**: Ensure Playwright browsers are installed

#### 🎯 **How It Works:**
1. **Smart Search Queries**: Uses targeted Google searches for executive profiles
   - `"Company Name" CEO OR founder site:linkedin.com/in/`
   - `"Company Name" executive site:twitter.com`
   - `"Company Name" CTO site:linkedin.com/in/`

2. **Profile Discovery**: Finds and validates social media profiles
3. **Data Extraction**: Extracts names, titles, and profile information
4. **Anti-Detection**: Includes captcha handling and stealth measures

#### 📄 **Output Format:**
Returns structured JSON with:
- `url`: Profile URL
- `name`: Person's name  
- `headline`: Job title/role
- `error`: Any processing errors

**Note**: LinkedIn cookies expire frequently - refresh them regularly for optimal results.

---

#### 🔗 **API Endpoints Reference:**

**Note**: For batch processing, we strongly recommend using the web interface above. These API endpoints are for direct integration and automation.

**1. Single Domain Request**
```http
POST /single-request
Content-Type: application/json
api-key: your_api_key

{"url": "example.com"}
```

**2. Multiple Domains**
```http
POST /array-request
Content-Type: application/json
api-key: your_api_key

{
  "domains": ["example1.com", "example2.com"],
  "max_workers": 5
}
```

**3. CSV Processing**
```http
POST /csv-request
Content-Type: application/json
api-key: your_api_key

{
  "csv_url": "https://example.com/domains.csv",
  "max_workers": 5
}
```

**4. Google Sheets**
```http
POST /sheet-request
Content-Type: application/json
api-key: your_api_key

{"target_url": "your_google_sheet_url"}
```

**5. Download Results**
```http
GET /download-csv/{filename}
api-key: your_api_key
```

### 🚀 **Production Deployment**

**With Gunicorn:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "Contact_extractor:app"
```

**With Docker:**
```bash
docker compose up -d
docker compose logs -f
```

## 🔧 Configuration

### 🌐 **Web Interface Settings**

The web interface provides extensive configuration options:

**File Upload Configuration:**
- **Max File Size**: 16MB for CSV/Excel uploads
- **Supported Formats**: CSV, XLSX, XLS
- **Upload Directory**: `uploads/` (auto-created)
- **Results Export**: `results/` (for CSV downloads)

**Processing Configuration:**
- **WebSocket Port**: 5001 (configurable in `web_interface.py`)
- **Session Management**: Automatic persistence and recovery
- **Progress Files**: `progress_files/` (for session state)
- **Thread Isolation**: Complete separation for browser instances

**Browser Settings:**
- **Headless Mode**: Enabled by default for performance
- **Captcha Handling**: Automatic browser visibility on detection
- **Anti-Detection**: Stealth mode with human-like behavior
- **Timeout**: 30 seconds per company (configurable)

### 🔑 **Environment Variables**

**Required Settings:**
```env
# API Authentication
MY_API_SECRET=your_secure_api_key_here

# CEO Discovery (Essential)
GOOGLE_COOKIES_PATH="google-cookie.json"
LINKEDIN_COOKIES_PATH="linkedin_cookies.json"
```

**Optional Settings:**
```env
# Google Sheets Integration
GOOGLE_SHEET_WORKER_URL=your_worker_url

# Proxy Configuration (for captcha bypass)
PROXY_URL="http://username:password@proxy.com:8080"

# Development Mode
DEBUG=False

# Custom Chrome Driver Path (if needed)
DRIVER_PATH=/usr/bin/chromedriver
```

### ⚙️ **Advanced Configuration**

**Browser Optimization** (in `company_contact_finder.py`):
```python
# Processing timeouts
PROCESSING_TIMEOUT = 30  # seconds per company
DELAY_BETWEEN_REQUESTS = 2  # seconds between requests

# Browser settings
HEADLESS_BROWSER = True  # invisible by default
ANTI_DETECTION = True  # stealth mode enabled
```

**UI Customization** (in `static/css/main.css`):
```css
:root {
    --primary: #2563eb;     /* Main brand color */
    --success: #059669;     /* Success messages */
    --warning: #d97706;     /* Warning states */
    --danger: #dc2626;      /* Error messages */
    --glow-intensity: 0.4;  /* Progress bar glow */
}
```

**Security Settings:**
- **File Validation**: Strict type and size checking
- **Path Sanitization**: Prevents directory traversal
- **Session Isolation**: Each processing session is isolated
- **CORS Protection**: Configurable cross-origin settings

## 📊 Output Format

### 🌐 **Web Interface Export (Primary)**

The web interface generates comprehensive CSV files with all discovered information:

#### 📄 **CSV Column Structure:**

| Column | Description | Example Data |
|--------|-------------|---------------|
| **Company Domain** | Primary website | `monad.xyz` |
| **Company Name** | Detected/provided name | `Monad Labs` |
| **Website Emails** | All contact emails found | `support@monad.xyz, hello@monad.xyz` |
| **Website Phones** | Contact numbers | `+1-555-0123, +1-555-0124` |
| **Website Social Links** | Social media JSON | `{"linkedin": "linkedin.com/company/monad", "twitter": "twitter.com/monadlabs"}` |
| **CEO LinkedIn** | Executive LinkedIn profile | `linkedin.com/in/keonehan` |
| **CEO Twitter/X** | Executive Twitter handle | `twitter.com/keonehan` |
| **CEO Instagram** | Executive Instagram | `instagram.com/keonehan` |
| **CEO TikTok** | Executive TikTok account | `tiktok.com/@keonehan` |
| **Processing Status** | Success/Error indicator | `Success`, `Error: Timeout` |
| **Timestamp** | Processing completion time | `2024-01-15 14:30:25` |

#### 📝 **Sample CSV Output:**
```csv
Company Domain,Company Name,Website Emails,Website Phones,Website Social Links,CEO LinkedIn,CEO Twitter/X,CEO Instagram,CEO TikTok,Processing Status,Timestamp
monad.xyz,Monad Labs,"support@monad.xyz, hello@monad.xyz",+1-555-0123,"{""linkedin"": ""linkedin.com/company/monad""}",linkedin.com/in/keonehan,twitter.com/keonehan,instagram.com/keonehan,,Success,2024-01-15 14:30:25
celestia.org,Celestia,contact@celestia.org,,"{""twitter"": ""twitter.com/celestiaorg""}",linkedin.com/in/mustafaal-bassam,twitter.com/musalbas,,,Success,2024-01-15 14:31:12
```

### 🔗 **API JSON Output**

For API integrations, the service returns structured JSON:

#### 📄 **Single Domain Response:**
```json
{
  "success": true,
  "message": "Processed 1 domain. CSV generated.",
  "csv_filename": "single_domain_1746616778.csv",
  "results": [
    {
      "domain": "monad.xyz",
      "logoURL": "https://monad.xyz/favicon.ico",
      "emails": ["support@monad.xyz", "hello@monad.xyz"],
      "phones": ["+1-555-0123"],
      "socialLinks": {
        "linkedin": "https://linkedin.com/company/monad",
        "twitter": "https://twitter.com/monadlabs",
        "instagram": "https://instagram.com/monadlabs"
      },
      "ceo_profiles": {
        "linkedin": "https://linkedin.com/in/keonehan",
        "twitter": "https://twitter.com/keonehan",
        "instagram": "https://instagram.com/keonehan"
      }
    }
  ]
}
```

#### 📊 **Batch Processing Response:**
```json
{
  "success": true,
  "message": "Processed 5 domains successfully.",
  "csv_filename": "batch_processing_1746616985.csv",
  "statistics": {
    "total_processed": 5,
    "successful": 4,
    "errors": 1,
    "emails_found": 12,
    "ceo_profiles_found": 7
  },
  "results": [
    {"domain": "monad.xyz", "status": "success", ...},
    {"domain": "celestia.org", "status": "success", ...},
    {"domain": "failed-domain.com", "status": "error", "error": "Timeout"}
  ]
}
```

### 📈 **Data Quality & Validation**

**Email Validation:**
- Format validation (RFC 5322 compliant)
- Domain validation
- Duplicate removal
- Common pattern recognition (support@, sales@, info@, etc.)

**Phone Number Processing:**
- International format standardization
- Invalid number filtering
- Duplicate removal
- Format: `+1-555-0123` or `+44-20-7946-0958`

**Social Media Links:**
- Platform-specific validation
- URL normalization
- Profile existence verification
- Structured JSON format for easy parsing

**CEO Profile Discovery:**
- Google search validation
- Profile accessibility verification
- Name and title extraction
- Platform-specific URL formatting

## 🔒 Security & Best Practices

### 🛡️ **Web Interface Security**

**File Upload Security:**
- **Strict validation**: Only CSV, XLSX, XLS files allowed
- **Size limits**: Maximum 16MB per upload
- **Path sanitization**: Prevents directory traversal attacks
- **Secure storage**: Temporary files in isolated upload directory
- **Auto-cleanup**: Uploaded files automatically removed after processing

**Session Security:**
- **Unique session IDs**: UUID-based session identification
- **Session isolation**: Each processing session runs independently
- **Progress encryption**: Session data securely stored
- **Auto-expiration**: Old sessions automatically cleaned up

**API Security:**
- **API key authentication**: Required for all API endpoints
- **Rate limiting**: Prevents abuse and overload
- **Input validation**: Comprehensive data validation
- **CORS protection**: Configurable cross-origin policies

### 🌐 **Web Scraping Ethics**

**Responsible Scraping:**
- **Respectful delays**: 2-second delays between requests
- **Robot.txt compliance**: Respects website scraping policies
- **User-agent identification**: Transparent browser identification
- **Timeout limits**: Prevents hanging on slow websites

**Anti-Detection Measures:**
- **Human-like behavior**: Realistic browsing patterns
- **Headless optimization**: Invisible unless captcha detected
- **Cookie management**: Maintains session state properly
- **Captcha handling**: Manual resolution when detected

### 📝 **Privacy & Data Handling**

**Data Protection:**
- **No data storage**: Results only saved temporarily
- **Local processing**: All extraction happens locally
- **Secure transmission**: HTTPS required for production
- **Data anonymization**: No personal data retention

**Cookie Management:**
- **Secure cookie storage**: Encrypted cookie files
- **Limited scope**: Cookies only for authentication
- **Regular refresh**: Expired cookies require manual update
- **Local-only**: Cookie files never transmitted

### 🔐 **Production Security Checklist**

**✅ Essential Steps:**
- [ ] Use HTTPS in production environment
- [ ] Generate strong API keys (32+ characters)
- [ ] Set up firewall rules for port access
- [ ] Configure rate limiting for API endpoints
- [ ] Monitor file upload directory for size
- [ ] Set up automated log rotation
- [ ] Enable CORS only for trusted domains
- [ ] Regular security updates for dependencies

**⚙️ Environment Configuration:**
```env
# Production settings
DEBUG=False
MY_API_SECRET=your_very_secure_api_key_here_32_chars_min
FLASK_ENV=production

# Security headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

**📊 Monitoring & Logging:**
- **Error tracking**: Comprehensive error logging
- **Performance monitoring**: Request timing and resource usage
- **Security alerts**: Failed authentication attempts
- **Usage analytics**: API endpoint usage statistics

---

## 🚀 Performance & Optimization

### ⚡ **Processing Performance**

**Batch Processing Optimization:**
- **Thread isolation**: Each company processed in separate thread
- **Memory efficiency**: Optimized for large company lists
- **Progressive results**: Results available immediately as processed
- **Auto-resume**: Interrupted sessions resume automatically

**Browser Performance:**
- **Headless by default**: Reduces memory usage by 60%
- **Smart captcha detection**: Browser only visible when needed
- **Connection pooling**: Reuses browser instances efficiently
- **Timeout management**: Prevents hanging on slow websites

**Recommended Batch Sizes:**
- **Small batches**: 10-20 companies (optimal for testing)
- **Medium batches**: 25-50 companies (balanced performance)
- **Large batches**: 100+ companies (enterprise processing)

### 📊 **Scalability**

**Horizontal Scaling:**
```bash
# Run multiple instances on different ports
python web_interface.py --port 5001
python web_interface.py --port 5002
python web_interface.py --port 5003
```

**Load Balancing:**
```nginx
upstream contact_finder {
    server localhost:5001;
    server localhost:5002;
    server localhost:5003;
}
```

**Docker Deployment:**
```bash
docker compose up --scale web=3
```

### 📈 **Monitoring & Analytics**

**Performance Metrics:**
- **Processing speed**: Average time per company
- **Success rate**: Percentage of successful extractions
- **Error tracking**: Common failure patterns
- **Resource usage**: Memory and CPU utilization

**Real-time Statistics:**
- **Live progress tracking**: WebSocket-based updates
- **Success/error counters**: Real-time success metrics
- **Processing logs**: Color-coded status messages
- **Export statistics**: Download completion tracking

---

## 🚀 Getting Started Guide

### 🎆 **5-Minute Quick Start**

1. **Install Contact Finder:**
   ```bash
   git clone https://github.com/yourusername/contact-finder.git
   cd contact-finder
   pip install -r requirements.txt requirements_web.txt
   playwright install
   ```

2. **Configure environment:**
   ```bash
   echo "MY_API_SECRET=your_secret_key" > .env
   echo "GOOGLE_COOKIES_PATH=google-cookie.json" >> .env
   ```

3. **Start the web interface:**
   ```bash
   python web_interface.py
   ```

4. **Open your browser:**
   - Navigate to `http://localhost:5001`
   - Upload your CSV file with company domains
   - Watch real-time processing and download results!

### 📁 **Sample Data**

Try Contact Finder with this sample CSV:
```csv
Company domains
monad.xyz
celestia.org
ritual.net
berachain.com
```

Expected results: 10+ emails, 4 CEO LinkedIn profiles, 3 Twitter accounts

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### 🛠️ **Core Technologies**
- **[Flask](https://flask.palletsprojects.com/)** - Lightweight web framework for Python
- **[Flask-SocketIO](https://flask-socketio.readthedocs.io/)** - Real-time WebSocket communication
- **[Playwright](https://playwright.dev/)** - Modern browser automation for CEO discovery
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML parsing and extraction
- **[Selenium WebDriver](https://selenium-python.readthedocs.io/)** - Legacy browser automation support

### 🌐 **Frontend Technologies**
- **HTML5** - Modern semantic markup with accessibility features
- **CSS3** - Advanced animations, gradients, and responsive design
- **JavaScript ES6+** - WebSocket client and interactive UI components
- **Progressive Enhancement** - Works without JavaScript for accessibility

### 📚 **Python Libraries**
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management
- **[pandas](https://pandas.pydata.org/)** - Data processing and CSV handling
- **[requests](https://docs.python-requests.org/)** - HTTP client for web scraping
- **[urllib3](https://urllib3.readthedocs.io/)** - Advanced HTTP connection pooling
- **[openpyxl](https://openpyxl.readthedocs.io/)** - Excel file processing

### 🎨 **Design & UX**
- **Responsive Design** - Mobile-first approach with CSS Grid and Flexbox
- **Professional UI** - Clean, modern interface with smooth animations
- **Accessibility** - WCAG compliant with screen reader support
- **Color-coded Feedback** - Intuitive status indicators and progress tracking

### 🚀 **Development Tools**
- **Thread Management** - Python threading for concurrent processing
- **Session Management** - Secure session handling with UUID generation
- **File Validation** - Comprehensive security checks for uploads
- **Error Handling** - Robust error management with user-friendly messages

### 🌟 **Special Features**
- **Real-time Processing** - Live progress updates via WebSockets
- **Smart Captcha Handling** - Automatic browser visibility management
- **Anti-Detection** - Stealth browsing with human-like behavior
- **Progressive Results** - Results available immediately as discovered
- **Auto-Resume** - Session persistence for interrupted processing

---

<div align="center">
  <h3>🎆 Contact Finder - Professional Contact Discovery Tool</h3>
  <p>Made with ❤️ by Mohammad | Powered by AI & Modern Web Technologies</p>
  
  <p>
    <strong>Transform your business outreach with intelligent contact discovery</strong><br>
    📧 Find emails • 👤 Discover CEOs • 🔗 Extract social profiles • 📊 Export results
  </p>
  
  <img src="https://img.shields.io/badge/Contact_Discovery-Professional-blue?style=for-the-badge" alt="Professional Contact Discovery">
  <img src="https://img.shields.io/badge/CEO_Profiles-AI_Powered-green?style=for-the-badge" alt="AI Powered CEO Discovery">
  <img src="https://img.shields.io/badge/Web_Interface-Modern-purple?style=for-the-badge" alt="Modern Web Interface">
</div> 
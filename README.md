# Contact Extractor API

<div align="center">
  <img src="https://github.com/mathofdynamic/Contact_Finder/blob/main/Screenshots/Contact_extractor_single_Request.png" alt="Contact Extractor Logo" width="600"/>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

## 📝 Overview

Contact Extractor is a powerful API service that automatically extracts contact information from websites, including:
- Email addresses
- Phone numbers
- Social media links (Instagram, LinkedIn, X/Twitter, Facebook, and more)
- Other contact-related data

The service provides multiple endpoints for different use cases, from single domain processing to batch processing via CSV or Google Sheets integration.

---

## 📸 Screenshots & Live Examples

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

- 🔍 **Intelligent Contact Detection**
  - Advanced email pattern recognition
  - Smart phone number validation
  - Social media link categorization
  - Footer-specific content analysis

- 🚀 **Multiple Processing Methods**
  - Single domain processing
  - Array of domains processing
  - CSV file processing
  - Google Sheets integration

- 🌐 **Professional Web Interface** (NEW!)
  - Modern, responsive web UI with drag & drop file upload
  - Real-time progress tracking with WebSocket updates  
  - Live results table that updates per domain processed
  - Pause/Resume functionality for large batches
  - Professional CSV export with comprehensive data
  - Live processing logs with color-coded messages
  - Progress persistence (resume interrupted sessions)
  - Multi-format support (CSV, XLSX, XLS files up to 16MB)
  - Smart column detection for company domains/names
  - Comprehensive data extraction per company
  - Interactive animations and professional UI/UX
  - Mobile-responsive design
  - Session management with automatic saving

- 🔒 **Security**
  - API key authentication
  - Secure request handling
  - Input validation

- 📊 **Output Options**
  - JSON response with extracted data
  - CSV file generation
  - Structured data format

- 🎯 **Lead Finding Tool**
  - Automated executive profile discovery
  - LinkedIn and Twitter profile scraping
  - Decision-maker contact information extraction
  - Google search automation with Playwright

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/contact-extractor.git
cd contact-extractor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers (for lead finding):
```bash
playwright install
```

5. Install web interface dependencies:
```bash
pip install -r requirements_web.txt
```

6. Create a `.env` file with your configuration:
```env
MY_API_SECRET=your_api_key_here
GOOGLE_SHEET_WORKER_URL=your_google_sheet_worker_url

# Cookie file paths for lead finding
GOOGLE_COOKIES_PATH="google-cookie.json"
LINKEDIN_COOKIES_PATH="linkedin_cookies.json"

# Optional: Proxy for captcha bypass (uncomment and configure if needed)
# PROXY_URL="http://username:password@proxy.com:8080"

# 'True' for debugging - Optional - Default: False
DEBUG=False

# Optional - e.g. '/usr/bin/chromedriver'
# Set the path if "driver not found" error is encountered.
DRIVER_PATH=path_to_chromedriver
```

## 🚀 Usage

### Starting the Server

```bash
python Contact_extractor.py
```

The server will start on `http://localhost:5000`

### Web Interface (Recommended for Batch Processing)

For an easier, more visual way to process multiple companies, use the professional web interface:

```bash
# Start the web interface
python3 web_interface.py
```

The web interface will be available at `http://localhost:5001`

#### 🌐 Web Interface Features:

- **📁 Smart File Upload**: Drag & drop CSV/XLSX/XLS files (up to 16MB)
- **🔄 Real-time Processing**: Live progress bar and statistics with WebSocket updates
- **📊 Live Results Table**: See results appear as companies are processed
- **⏸️ Pause/Resume**: Stop and continue processing anytime
- **📋 Live Logs**: Color-coded processing messages in real-time
- **💾 Progress Persistence**: Resume interrupted sessions automatically
- **📄 Professional CSV Export**: Download results anytime during or after processing
- **🎨 Modern UI/UX**: Professional design with smooth animations
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **🔍 Smart Detection**: Automatically detects company domain/name columns
- **🛡️ Security**: File validation, session isolation, secure uploads
- **⚡ Performance**: Background processing with threading support
- **📈 Analytics**: Real-time statistics and success/error tracking

#### 📝 Supported CSV Format:
```csv
Company domains
monad.xyz
eigenlayer.xyz
celestia.org
ritual.net
berachain.com
```

#### 📊 What Gets Extracted Per Company:
- 📧 **Website Emails**
- 📞 **Phone Numbers**
- 🔗 **Social Media Links**
- 👤 **CEO LinkedIn Profile**
- 🐦 **CEO Twitter/X Profile**
- 📸 **CEO Instagram Profile**
- 🎵 **CEO TikTok Profile**

#### 🎯 Web Interface Workflow:
1. **Upload CSV**: Drag & drop or browse for your company list
2. **Preview**: Review detected companies and column selection
3. **Start Processing**: Begin extraction with one click
4. **Monitor**: Watch real-time progress, live results, and processing logs
5. **Control**: Pause/resume processing anytime as needed
6. **Download**: Get professional CSV export with comprehensive data

#### 🛠️ Web Interface Technical Details:

**Backend Architecture:**
- Flask application with SocketIO for real-time communication
- Background processing using Python threading
- Session management with persistent progress tracking
- Secure file upload and validation
- RESTful API endpoints for all operations

**Frontend Technology:**
- Modern HTML5 with semantic, accessible markup
- CSS3 with smooth animations and transitions
- JavaScript ES6+ with WebSocket client integration
- Responsive design with mobile-first approach
- Progressive enhancement (works without JavaScript)

**Data Flow:**
1. File Upload → Parsed and validated
2. Session Creation → Unique session ID generated
3. Background Processing → Companies processed in separate thread
4. WebSocket Updates → Real-time progress and results
5. CSV Export → Continuous saving and download capability

**Security Features:**
- File type and size validation (16MB max)
- Secure upload directory with path sanitization
- Session isolation and CORS protection
- Prevention of directory traversal attacks

#### 🔧 Web Interface Configuration:

**File Upload Settings:**
```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
```

**Processing Settings:**
```python
# Adjust timeout and delays in company_contact_finder.py
PROCESSING_TIMEOUT = 30  # seconds per company
DELAY_BETWEEN_REQUESTS = 2  # seconds
```

**UI Customization:**
```css
/* Modify colors in static/css/main.css */
:root {
    --primary: #2563eb;
    --success: #059669;
    --warning: #d97706;
    --danger: #dc2626;
}
```

#### 🚨 Web Interface Troubleshooting:

**Common Issues:**

1. **"WebSocket connection failed"**
   - Check if port 5001 is available
   - Ensure firewall allows connections
   - Try restarting the application

2. **"Failed to process companies"**
   - Verify internet connection
   - Check if Playwright browsers are installed: `playwright install`
   - Review browser console for errors

3. **"File upload failed"**
   - Check file size (max 16MB)
   - Ensure file format is CSV/XLSX/XLS
   - Verify file is not corrupted

4. **"No companies detected"**
   - Check CSV format and encoding
   - Ensure first row contains company domains/names
   - Try different column if detection is wrong

**Performance Tips:**
- Optimal batch size: 10-50 companies per batch
- Ensure stable internet connection for web scraping
- Close unnecessary browser tabs when processing
- Regular automatic saves prevent data loss

#### 📊 Web Interface Data Output:

The web interface extracts comprehensive data for each company:

**Company Website Data:**
- All email addresses found on the website
- Contact phone numbers (validated for accuracy)
- Social media links (all platforms)
- Company logo URL

**CEO/Executive Profiles:**
- LinkedIn profile URL
- Twitter/X profile URL
- Instagram profile URL
- TikTok profile URL

**CSV Export Format:**
Results are exported with these columns:
- Company Domain
- Company Name  
- Website Emails
- Website Phones
- Website Social Links
- CEO LinkedIn
- CEO Twitter/X
- CEO Instagram
- CEO TikTok
- Processing Status
- Timestamp

### Lead Finding Tool

The project includes a standalone lead finding script that uses Playwright to discover and scrape contact information for decision-makers at specific companies.

#### Basic Usage
```bash
python lead_finder.py
```

#### Setup for Lead Finding
1. **Google Cookies**: You already have `google-cookie.json` in your project
2. **LinkedIn Cookies**: Export cookies from LinkedIn using a browser extension and save as `linkedin_cookies.json`
3. **Environment Variables**: Ensure your `.env` file includes the cookie paths
4. **Captcha Handling**: The script includes automatic captcha detection and manual solving options

#### How Lead Finding Works
1. **Google Search Phase**: Uses targeted search queries to find LinkedIn and Twitter profiles
2. **Profile Scraping**: Navigates to each profile and extracts key information
3. **Data Output**: Displays results in structured JSON format

#### Search Queries Used
- `"Company Name" CEO OR founder site:linkedin.com/in/`
- `"Company Name" executive site:twitter.com`
- `"Company Name" CTO site:linkedin.com/in/`

#### Output Format
The script outputs a list of dictionaries containing:
- `url`: Profile URL
- `name`: Person's name
- `headline`: Job title/headline
- `error`: Error message if scraping failed

**Note**: LinkedIn cookies expire frequently, so refresh them regularly for best results.

#### Captcha Handling Strategies
The script includes several strategies to handle Google's captcha challenges:

1. **Automatic Detection**: Detects various types of captchas and unusual activity warnings
2. **Manual Solving**: Pauses execution and waits for you to solve captchas manually in the browser
3. **Anti-Detection Measures**: 
   - User agent rotation
   - Human-like delays and behavior
   - Stealth mode with browser fingerprinting evasion
   - Proxy support (configurable)
4. **Fallback Options**: Can switch to alternative search engines if Google blocks access

#### Configuration Options
Edit `captcha_config.py` to customize:
- User agent rotation
- Delay timing
- Proxy settings
- Search fallbacks
- Rate limiting

Example production startup with Gunicorn:
```
gunicorn -w 4 -b 0.0.0.0:5000 "Contact_extractor:app"
```

Example production startup using Docker:
```
docker compose up -d
docker compose logs -f # Run to see logs
```

### API Endpoints

**Note**: For batch processing, we recommend using the web interface above. The API endpoints below are for direct integration.

#### 1. Single Domain Request
Process a single domain for contact information.

**Request:**
```http
POST /single-request
Content-Type: application/json
api-key: your_api_key

{
    "url": "example.com"
}
```

#### 2. Array Request
Process multiple domains in parallel.

**Request:**
```http
POST /array-request
Content-Type: application/json
api-key: your_api_key

{
    "domains": ["example1.com", "example2.com"],
    "max_workers": 5
}
```

#### 3. CSV Request
Process domains from a CSV file.

**Request:**
```http
POST /csv-request
Content-Type: application/json
api-key: your_api_key

{
    "csv_url": "https://example.com/domains.csv",
    "domain_column_header": "Domain",
    "max_workers": 5
}
```

#### 4. Sheet Request
Process domains from a Google Sheet.

**Request:**
```http
POST /sheet-request
Content-Type: application/json
api-key: your_api_key

{
    "target_url": "your_google_sheet_url",
    "max_workers": 5
}
```

#### 5. Download CSV
Download generated CSV files.

```http
GET /download-csv/{filename}
api-key: your_api_key
```

## 🔧 Configuration

### Environment Variables

- `MY_API_SECRET`: Your API key for authentication
- `GOOGLE_SHEET_WORKER_URL`: URL for Google Sheets integration
- `GOOGLE_COOKIES_PATH`: Path to Google cookies file for lead finding
- `LINKEDIN_COOKIES_PATH`: Path to LinkedIn cookies file for lead finding
- `DEBUG`: Set to `True` for development mode (optional)

### Web Interface Configuration

The web interface uses additional settings:
- **Upload Directory**: `uploads/` (auto-created)
- **Progress Files**: `progress_files/` (for session persistence)
- **Results Export**: `results/` (for CSV downloads)
- **Max File Size**: 16MB for CSV/Excel uploads
- **WebSocket Port**: 5001 (configurable in web_interface.py)
- **Session Management**: Automatic session persistence and recovery

### Chrome Options

The service uses headless Chrome for web scraping with the following configurations:
- Headless mode
- No sandbox
- Disabled GPU
- Custom user agent

## 📊 Output Format

### API CSV Output
The API CSV output includes the following columns:
- Domain
- Emails
- Phone Numbers
- Instagram
- LinkedIn
- X (Twitter)
- Facebook
- Other Socials

### Web Interface CSV Output
The web interface provides enhanced CSV export with:
- Company Domain
- Company Name
- Website Emails
- Website Phones
- Website Social Links
- CEO LinkedIn
- CEO Twitter/X
- CEO Instagram
- CEO TikTok
- Processing Status
- Timestamp

## 🔒 Security Considerations

1. Always use HTTPS in production
2. Keep your API key secure
3. Validate all input data
4. Monitor request rates
5. Implement rate limiting if needed

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask framework
- Selenium WebDriver
- BeautifulSoup4
- Python-dotenv
- Playwright (for lead finding automation)

---

<div align="center">
  Made with ❤️ by Mohammad
</div> 
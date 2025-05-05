# Contact Extractor

A powerful web scraping API service designed to extract contact information (emails, phone numbers) and social media links from websites.

## Overview

Contact Extractor is a Flask-based API service that scrapes websites to extract:
- Email addresses
- Phone numbers
- Social media links (Instagram, LinkedIn, X/Twitter, and other platforms)

It uses Selenium with headless Chrome for robust scraping, BeautifulSoup for HTML parsing, and multithreading for efficient parallel processing of multiple domains.

## Features

- **Bulk Domain Processing**: Process multiple domains in parallel
- **Smart Extraction**: Uses both link analysis and regex pattern matching
- **Social Media Detection**: Identifies and categorizes links to 20+ social platforms
- **CSV Export**: Automatically exports results to downloadable CSV files
- **API Authentication**: Secure endpoints with API key authentication
- **Integration-Ready**: Designed to work with external data sources via a worker URL

## Requirements

- Python 3.6+
- Chrome/Chromium browser
- ChromeDriver compatible with your Chrome version

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Contact_Extractor
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API secret:
```
MY_API_SECRET=your_secret_key_here
```

4. Ensure ChromeDriver is installed and matches your Chrome version.

## Running the Application

Start the Flask server:
```bash
python Contact_extractor.py
```

By default, the server runs on `http://localhost:5000` in debug mode.

## API Endpoints

### 1. Process Multiple Domains

**Endpoint**: `/process-domains`  
**Method**: POST  
**Authentication**: API key required in headers

**Request Headers**:
```
api-key: your_secret_key_here
```

**Request Body**:
```json
{
  "worker_url": "https://your-worker-service.com/endpoint",
  "target_url": "https://docs.google.com/spreadsheets/d/...",
  "max_workers": 5
}
```

- `worker_url`: URL of a service that returns domains to process
- `target_url`: URL that the worker service will use to fetch domains (e.g., a Google Sheet)
- `max_workers`: Number of parallel processes (default: 5)

**Response**:
```json
{
  "success": true,
  "message": "Processed 50 domains",
  "csv_filename": "domain_contacts_1234567890.csv",
  "results": [
    {
      "domain": "example.com",
      "emails": ["contact@example.com", "support@example.com"],
      "phones": ["+1-555-123-4567"],
      "instagram": "https://instagram.com/example",
      "linkedin": "https://linkedin.com/company/example",
      "x": "https://x.com/example",
      "other": ["https://facebook.com/example"]
    },
    ...
  ]
}
```

### 2. Download CSV Results

**Endpoint**: `/download-csv/<filename>`  
**Method**: GET  
**Authentication**: API key required in headers

**Request Headers**:
```
api-key: your_secret_key_here
```

Returns a CSV file with the following columns:
- Domain
- Emails
- Phone Numbers
- Instagram
- LinkedIn
- X
- Other Socials

### 3. Extract Info from a Single Domain

**Endpoint**: `/extract-info`  
**Method**: POST  
**Authentication**: API key required in headers

**Request Headers**:
```
api-key: your_secret_key_here
```

**Request Body**:
```json
{
  "url": "https://example.com"
}
```

**Response**:
```json
{
  "emails": ["contact@example.com"],
  "phone_numbers": ["+1-555-123-4567"],
  "social_links": ["https://instagram.com/example", "https://linkedin.com/company/example"]
}
```

## Worker Service Integration

The application is designed to work with an external "worker" service that provides the list of domains to process. This worker must:

1. Accept a POST request with a JSON body containing a `url` parameter (typically a Google Sheet URL)
2. Return a JSON response with:
   ```json
   {
     "success": true,
     "domains": ["example.com", "example.org", "example.net"]
   }
   ```

## Supported Social Media Platforms

The application can identify links to the following platforms:
- X/Twitter
- Facebook
- Instagram
- LinkedIn
- YouTube
- Pinterest
- TikTok
- Snapchat
- Reddit
- Tumblr
- WhatsApp
- Telegram
- Discord
- Medium
- GitHub
- Threads
- Mastodon
- And more

## Technical Implementation

### Extraction Process
1. **Initialization**: Configures a headless Chrome instance with Selenium
2. **Page Loading**: Visits the target domain with timeouts and error handling
3. **Content Extraction**:
   - Parses links for social media, email, and phone information
   - Applies regex patterns to find contact details in page text
   - Categorizes social media links by platform
4. **Result Organization**: Structures data for API response and CSV export

### Multithreading
Uses Python's `ThreadPoolExecutor` for parallel processing of multiple domains, with configurable worker count to manage system resources.

### Error Handling
Implements robust error handling to ensure the process continues even if individual domain scraping fails.

## Security Considerations

- All API endpoints are protected with API key authentication
- The API key is loaded from environment variables, not hardcoded
- The application runs in a sandboxed Chrome environment with appropriate security flags

## CSV Format

The generated CSV file contains the following columns:
- **Domain**: The website domain (without protocol)
- **Emails**: Semicolon-separated list of email addresses
- **Phone Numbers**: Semicolon-separated list of phone numbers
- **Instagram**: Instagram profile URL (if found)
- **LinkedIn**: LinkedIn profile URL (if found)
- **X**: X/Twitter profile URL (if found)
- **Other Socials**: Semicolon-separated list of other social media links

## Limitations

- JavaScript-heavy websites may not fully render in headless mode
- Some websites actively block scraping attempts
- Rate limiting may occur if processing too many domains from the same IP
- Regex patterns may not catch all variations of contact information

## License

[Specify your license information here]

## Contributing

[Specify contribution guidelines here] 
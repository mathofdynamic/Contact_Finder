# Contact Extractor API

<div align="center">
  <img src="screenshots/Contact_extractor_single_Request.png" alt="Contact Extractor Logo" width="600"/>
  
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
      "emails": ["support@droplinked.com"],
      "facebook": "",
      "instagram": "https://www.instagram.com/drop_linked",
      "linkedin": "https://www.linkedin.com/company/droplinked",
      "other": [
        "https://discord.com/channels/...",
        "https://t.me/droplinked"
      ],
      "phones": [],
      "x": "https://twitter.com/droplinked"
    }
  ],
  "success": true
}
```
![Single Domain Request Screenshot](screenshots/Contact_extractor_single_Request.png)
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
  "max_workers": 3
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
![Array Request Screenshot](screenshots/Contact_extractor_Array.png)
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
![CSV Request Screenshot](screenshots/Contact_extractor_CSV_request.png)
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
![Sheet Request Screenshot](screenshots/Contact_extractor_Sheet.png)
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

- 🔒 **Security**
  - API key authentication
  - Secure request handling
  - Input validation

- 📊 **Output Options**
  - JSON response with extracted data
  - CSV file generation
  - Structured data format

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

4. Create a `.env` file with your configuration:
```env
MY_API_SECRET=your_api_key_here
GOOGLE_SHEET_WORKER_URL=your_google_sheet_worker_url
```

## 🚀 Usage

### Starting the Server

```bash
python Contact_extractor.py
```

The server will start on `http://localhost:5000`

### API Endpoints

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

### Chrome Options

The service uses headless Chrome for web scraping with the following configurations:
- Headless mode
- No sandbox
- Disabled GPU
- Custom user agent

## 📊 Output Format

The CSV output includes the following columns:
- Domain
- Emails
- Phone Numbers
- Instagram
- LinkedIn
- X (Twitter)
- Facebook
- Other Socials

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

---

<div align="center">
  Made with ❤️ by [Your Name]
</div> 
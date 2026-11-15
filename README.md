# SEO Analyzer

A Django-based web application for automated technical SEO analysis of websites, integrated with Google PageSpeed Insights API.

## Features

**Custom SEO Analysis**
- Meta title and description analysis
- H1/H2 heading validation
- Empty heading detection
- Image ALT attribute analysis
- HTTPS detection
- Internal and external link counting
- Custom SEO score (0–100)

**Google PageSpeed Insights Integration**
- Performance score
- Accessibility score
- Best Practices score
- SEO score
- Mobile Lighthouse analysis

**Web Dashboard**
- Website URL input form
- SEO score visualization
- Detailed technical SEO results
- Color-coded check statuses
- Error handling for unavailable websites and API failures

## Tech Stack

- Python
- Django
- BeautifulSoup4
- Requests
- Google PageSpeed Insights API
- Bootstrap 5
- SQLite

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_NAME
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
GOOGLE_PAGESPEED_API_KEY=your_google_api_key
```

Enable the PageSpeed Insights API in your Google Cloud project.

Run database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## How It Works

1. The user enters a website URL.
2. The Django backend validates the URL and retrieves the HTML.
3. BeautifulSoup parses the page.
4. Custom SEO checks analyze metadata, headings, images, links, and HTTPS.
5. The application calculates a weighted SEO score.
6. Google PageSpeed Insights provides independent Lighthouse scores.
7. Results are displayed in a dashboard.

## Limitations

- Analyzes one webpage at a time rather than crawling an entire website.
- Custom SEO scoring uses project-defined heuristics, not Google's ranking algorithm.
- Google Lighthouse scores may vary between runs.
- JavaScript-rendered content may not be fully represented in the HTML analysis.
- URL validation is preliminary and does not provide complete SSRF protection. Public deployment requires additional network-level safeguards and secure DNS handling.

## Project Status

Functional MVP intended for local demonstration and further development.
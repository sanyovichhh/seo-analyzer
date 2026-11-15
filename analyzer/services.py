import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from django.conf import settings
from .security import validate_public_url


logger = logging.getLogger(__name__)

def analyze_google_pagespeed(url: str):
    endpoint = (
        "https://www.googleapis.com/"
        "pagespeedonline/v5/runPagespeed"
    )

    params = [
        ("url", url),
        ("strategy", "mobile"),
        ("category", "performance"),
        ("category", "accessibility"),
        ("category", "best-practices"),
        ("category", "seo"),
    ]

    api_key = settings.GOOGLE_PAGESPEED_API_KEY

    if not api_key:
        return {
            "success": False,
            "error": "PageSpeed API key is not configured"
        }

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers={"X-goog-api-key": api_key},
            timeout=90
        )
        response.raise_for_status()

        data = response.json()
        lighthouse = data.get("lighthouseResult", {})

        if lighthouse.get("runtimeError"):
            return {
                "success": False,
                "error": "Google Lighthouse analysis failed"
            }

        categories = lighthouse.get("categories", {})

        scores = {}

        for category in [
            "performance",
            "accessibility",
            "best-practices",
            "seo"
        ]:
            value = categories.get(category, {}).get("score")

            scores[category] = (
                round(value * 100)
                if value is not None
                else None
            )

        if all(value is None for value in scores.values()):
            return {
                "success": False,
                "error": "No Lighthouse scores returned"
            }

        return {
            "success": True,
            "strategy": "mobile",
            "scores": scores
        }

    except requests.HTTPError as exc:
        logger.error(
            "PageSpeed HTTP error: %s",
            exc.response.status_code if exc.response is not None else "unknown"
        )
        return {
            "success": False,
            "error": "Google PageSpeed HTTP request failed"
        }

    except (requests.RequestException, ValueError) as exc:
        logger.error("PageSpeed error: %s", type(exc).__name__)
        return {
            "success": False,
            "error": "Google PageSpeed is unavailable"
        }

def calculate_seo_score(analysis_results):
    score = 0
    
    status_multipliers = {
        "success": 1,
        "warning": 0.5,
        "error": 0
    }

    checks = {
        "title": analysis_results.get("meta", {}).get("title", {}),
        "description": analysis_results.get("meta", {}).get("description", {}),
        "h1": analysis_results.get("headings", {}).get("h1", {}),
        "h2": analysis_results.get("headings", {}).get("h2", {}),
        "images": analysis_results.get("images", {}),
        "https": analysis_results.get("https", {})
    }

    weights = {
        "title": 20,
        "description": 20,
        "h1": 20,
        "h2": 10,
        "images": 15,
        "https": 15
    }
    for check_name, check_result in checks.items():
        status = check_result.get("status")

        if status not in status_multipliers:
            logger.warning(
                "Missing or invalid status for %s",
                check_name
            )
            return None

        score += weights[check_name] * status_multipliers[status]
    return score   


def analyze_website(url):
    html  = fetch_website(url)
    if html is None:
        return {
            "success": False,
            "error": "Failed to fetch website"
        }
    soup = parse_html(html)
    results = {
        "meta": analyze_meta(soup),
        "headings": analyze_headings(soup),
        "images": analyze_images(soup),
        "links": analyze_links(soup, url),
        "https": analyze_https(url)
    }
    
    score = calculate_seo_score(results)
    if score is None:
        return {
            "success": False,
            "error": "Failed to calculate SEO score"
        }
    
    return {
        "success": True,
        "url": url,
        "score": score,
        "results": results
    }


def fetch_website(url):
    if not validate_public_url(url):
        logger.warning("Invalid or non-public URL")
        return None

    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=False,
            headers={
                "User-Agent": "SEOAnalyzer/1.0 (educational project)"
            }
        )

        logger.info(
            "Fetch status for %s: %s",
            url,
            response.status_code
        )

        response.raise_for_status()

        if 300 <= response.status_code < 400:
            logger.warning("Redirect not supported")
            return None

        content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            return None

        return response.text

    except requests.HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )

        logger.warning(
            "Website returned HTTP %s",
            status
        )
        return None

    except requests.RequestException as exc:
        logger.warning(
            "Website fetch failed: %s",
            type(exc).__name__
        )
        return None

def parse_html(html):
    return BeautifulSoup(html, "html.parser")


def analyze_meta(soup: BeautifulSoup):
    result = {
        "title": {},
        "description": {}
    }
    title = soup.title.get_text(strip=True) if soup.title else None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    
    # Analyze title
    if not title:
        result["title"]["value"] = ""
        result["title"]["status"] = "error"
        result["title"]["message"] = "Title is empty"
    elif len(title) > 60:
        result["title"]["value"] = title
        result["title"]["status"] = "warning"
        result["title"]["message"] = "Title is too long"
    elif len(title) < 30:
        result["title"]["value"] = title
        result["title"]["status"] = "warning"
        result["title"]["message"] = "Title is too short"
    else:
        result["title"]["value"] = title
        result["title"]["status"] = "success"
        result["title"]["message"] = "Title is of optimal length"
    
    # Analyze description
    if not meta_tag or not meta_tag.get("content"):
        result["description"]["value"] = ""
        result["description"]["status"] = "error"
        result["description"]["message"] = "Description is empty"
    else:
        description = meta_tag["content"].strip()
        if len(description) > 160:
            result["description"]["value"] = description
            result["description"]["status"] = "warning"
            result["description"]["message"] = "Description is too long"
        elif len(description) < 120:
            result["description"]["value"] = description
            result["description"]["status"] = "warning"
            result["description"]["message"] = "Description is too short"
        else:
            result["description"]["value"] = description
            result["description"]["status"] = "success"
            result["description"]["message"] = "Description is of optimal length"
    
    return result

def analyze_headings(soup: BeautifulSoup):
    h1_array = soup.find_all("h1")
    h2_array = soup.find_all("h2")
    result = {
        "h1": {
            "value": [h1.get_text(strip=True) for h1 in h1_array],
            "count": len(h1_array),
            "status": "",
            "message": "One H1 heading found" if len(h1_array) == 1 else f"{len(h1_array)} H1 headings found"
        },
        "h2": {
            "value": [h2.get_text(strip=True) for h2 in h2_array],
            "count": len(h2_array),
            "status": "success" if len(h2_array) > 0 else "warning",
            "message": "H2 headings found" if len(h2_array) > 0 else "No H2 headings found"
        },
        "empty_headings": {
            "value": 0,
            "status": "success",
            "message": "No empty headings found"
        }
    }
    if result["h1"]["count"] == 0:
        result["h1"]["status"] = "error"
    elif result["h1"]["count"] > 1:
        result["h1"]["status"] = "warning"
    else:
        result["h1"]["status"] = "success"
    
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if not tag.get_text(strip=True):
            result["empty_headings"]["value"] += 1
            result["empty_headings"]["status"] = "warning"
            result["empty_headings"]["message"] = "Empty headings found"
    
    return result
    
def analyze_images(soup:BeautifulSoup):

    images = soup.find_all("img")
    result = {
        "total_images": len(images),
        "with_alt": 0,
        "without_alt": 0,
        "empty_alt": 0,
        "status": "",
        "message": "No images found"
    }

    for img in images:
        alt_text = img.get("alt")
        if alt_text is None:
            result["without_alt"] += 1
        elif alt_text.strip() == "":
            result["empty_alt"] += 1
        else:
            result["with_alt"] += 1
    if result["without_alt"] > 0:
        result["status"] = "error"
        result["message"] = "Some images need ALT attribute review"
    elif result["empty_alt"] > 0:
        result["status"] = "warning"
        result["message"] = "Some images have empty ALT attributes"
    else:
        result["status"] = "success"
        result["message"] = "All images have ALT attributes"
    return result

def analyze_links(soup: BeautifulSoup, url: str):
    links = soup.find_all("a", href=True)

    result = {
        "total": 0,
        "internal": 0,
        "external": 0,
        "status": "success",
        "message": "Links analyzed successfully"
    }

    base_domain = urlparse(url).hostname

    if not base_domain:
        return {
            **result,
            "status": "error",
            "message": "Invalid website URL"
        }

    base_domain = base_domain.lower().removeprefix("www.")

    for link in links:
        href = link.get("href", "").strip()

        if not href:
            continue

        absolute_url = urljoin(url, href)
        parsed_link = urlparse(absolute_url)

        if parsed_link.scheme.lower() not in ("http", "https"):
            continue

        link_domain = parsed_link.hostname

        if not link_domain:
            continue

        link_domain = link_domain.lower().removeprefix("www.")

        result["total"] += 1

        if link_domain == base_domain:
            result["internal"] += 1
        else:
            result["external"] += 1

    return result        
            
def analyze_https(url: str):
    result = {
        "status": "",
        "message": ""
    }
    parsed_url = urlparse(url)
    if parsed_url.scheme.lower() == "https":
        result["status"] = "success"
        result["message"] = "Website is using HTTPS"
    else:
        result["status"] = "error"
        result["message"] = "Website is not using HTTPS"
    return result


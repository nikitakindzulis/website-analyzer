import csv
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebsiteAnalyzer/1.0)"
}


def fetch_html(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def get_meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": name})

    if tag and tag.get("content"):
        return tag["content"].strip()

    return ""


def get_title(soup: BeautifulSoup) -> str:
    title_tag = soup.find("title")

    if title_tag:
        return title_tag.get_text(strip=True)

    return ""


def get_main_heading(soup: BeautifulSoup) -> str:
    h1_tag = soup.find("h1")

    if h1_tag:
        return h1_tag.get_text(strip=True)

    return ""


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_contacts(text: str) -> dict:
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\+?\d[\d\s().-]{7,}\d"

    emails = sorted(set(re.findall(email_pattern, text)))
    phones = sorted(set(re.findall(phone_pattern, text)))

    return {
        "emails": emails[:5],
        "phones": phones[:5]
    }


def count_links(soup: BeautifulSoup, base_url: str) -> dict:
    base_domain = urlparse(base_url).netloc

    internal_count = 0
    external_count = 0

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if not href or href.startswith("#"):
            continue

        if href.startswith("/"):
            internal_count += 1
        elif href.startswith("http"):
            link_domain = urlparse(href).netloc

            if link_domain == base_domain:
                internal_count += 1
            else:
                external_count += 1

    return {
        "total_links": internal_count + external_count,
        "internal_links": internal_count,
        "external_links": external_count
    }


def count_images(soup: BeautifulSoup) -> dict:
    images = soup.find_all("img")
    images_without_alt = 0

    for image in images:
        alt = image.get("alt", "")

        if not alt.strip():
            images_without_alt += 1

    return {
        "total_images": len(images),
        "images_without_alt": images_without_alt
    }


def extract_keyword_sentences(text: str, keyword: str, limit: int = 10) -> list[str]:
    if not keyword:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    keyword_lower = keyword.lower()
    matched_sentences = []

    for sentence in sentences:
        if keyword_lower in sentence.lower():
            cleaned_sentence = sentence.strip()

            if cleaned_sentence:
                matched_sentences.append(cleaned_sentence)

    return matched_sentences[:limit]


def analyze_keyword(text: str, keyword: str) -> dict:
    if not keyword:
        return {
            "keyword": "",
            "found": False,
            "count": 0,
            "sentences": []
        }

    text_lower = text.lower()
    keyword_lower = keyword.lower()

    count = text_lower.count(keyword_lower)
    sentences = extract_keyword_sentences(text, keyword)

    return {
        "keyword": keyword,
        "found": count > 0,
        "count": count,
        "sentences": sentences
    }


def analyze_website(url: str, keyword: str) -> dict:
    html = fetch_html(url)

    if html is None:
        return {
            "url": url,
            "status": "failed",
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "Failed to load website"
        }

    soup = BeautifulSoup(html, "lxml")

    full_page_text = clean_text(soup.get_text(separator=" "))

    title = get_title(soup)
    description = get_meta_content(soup, "description")
    main_heading = get_main_heading(soup)

    return {
        "url": url,
        "status": "success",
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "page_info": {
            "title": title,
            "description": description,
            "main_heading": main_heading,
            "word_count": len(full_page_text.split())
        },

        "contacts": extract_contacts(full_page_text),
        "links": count_links(soup, url),
        "images": count_images(soup),
        "keyword": analyze_keyword(full_page_text, keyword)
    }


def save_json(report: dict, filename: Path) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=4)


def save_csv(report: dict, filename: Path) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["Category", "Field", "Value"])

        writer.writerow(["General", "URL", report.get("url", "")])
        writer.writerow(["General", "Status", report.get("status", "")])
        writer.writerow(["General", "Analyzed at", report.get("analyzed_at", "")])

        if report.get("status") == "failed":
            writer.writerow(["General", "Error", report.get("error", "")])
            return

        writer.writerow(["Page", "Title", report["page_info"]["title"]])
        writer.writerow(["Page", "Description", report["page_info"]["description"]])
        writer.writerow(["Page", "Main heading", report["page_info"]["main_heading"]])
        writer.writerow(["Page", "Word count", report["page_info"]["word_count"]])

        writer.writerow(["Contacts"])

        if report["contacts"]["emails"]:
            writer.writerow([
                "Contacts",
                "Emails",
                ", ".join(report["contacts"]["emails"])
            ])

        if report["contacts"]["phones"]:
            writer.writerow([
                "Contacts",
                "Phones",
                ", ".join(report["contacts"]["phones"])
            ])

        writer.writerow(["Total links", report["links"]["total_links"]])
        writer.writerow(["Total images", report["images"]["total_images"]])

        writer.writerow(["Keyword", report["keyword"]["keyword"]])
        writer.writerow(["Keyword Count", report["keyword"]["count"]])

        for index, sentence in enumerate(report["keyword"]["sentences"], start=1):
            writer.writerow([
                f"Keyword Sentence {index}",
                sentence
            ])


def create_report_filenames(url: str) -> tuple[Path, Path]:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    domain = urlparse(url).netloc.replace(".", "_")

    if not domain:
        domain = "website"

    json_filename = reports_dir / f"{domain}_report.json"
    csv_filename = reports_dir / f"{domain}_report.csv"

    return json_filename, csv_filename


def main():
    url = input("Enter website URL: ").strip()
    keyword = input("Enter keyword: ").strip()

    if not url.startswith("http"):
        url = "https://" + url

    report = analyze_website(url, keyword)

    json_filename, csv_filename = create_report_filenames(url)

    save_json(report, json_filename)
    save_csv(report, csv_filename)

    print("Reports saved successfully.")


if __name__ == "__main__":
    main()
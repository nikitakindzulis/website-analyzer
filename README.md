# Website Analyzer

Website Analyzer is a simple Python tool that analyzes a web page and saves the result as CSV and JSON reports.

## Features

- Extracts page title, meta description and main heading
- Counts total words on the page
- Extracts emails and phone numbers
- Counts total links and images
- Searches for a keyword on the page
- Saves sentences that contain the selected keyword
- Exports results to CSV and JSON

## Technologies

- Python
- Requests
- BeautifulSoup
- lxml
- CSV
- JSON
- Regular expressions

## Installation

Clone the repository:

git clone https://github.com/nikitakindzulis/website-analyzer.git
cd website-analyzer

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

## Usage

Run the script:

python parser.py

Then enter a website URL and a keyword:

Enter website URL: https://en.wikipedia.org/wiki/7-Eleven
Enter keyword: Japan

The tool will create reports in the reports folder:

reports/example_report.csv
reports/example_report.json

## Example Output

The CSV report includes:

Category,Field,Value
General,URL,https://en.wikipedia.org/wiki/7-Eleven
General,Status,success
Page,Title,7-Eleven - Wikipedia
Page,Main heading,7-Eleven
Page,Word count,13707
Contacts,Phones,"0040-7909, 1353830071"
Total links,1324
Total images,38
Keyword,Japan
Keyword Count,42
Keyword Sentence 1,"Example sentence containing the keyword."

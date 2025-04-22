import requests
import re
import os
from PyPDF2 import PdfMerger 
from io import BytesIO
from playwright.sync_api import sync_playwright

TOKEN = "3d887eb9d03345709d279836a8be130e"

# Only for local use, in case token changes
def get_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  
        context = browser.new_context()
        page = context.new_page()
        token_found = None

        # Hook to listen to network responses
        def handle_response(response):
            url = response.url
            if 'channelToken=' in url:
                match = re.search(r'channelToken=([a-f0-9]+)', url)
                if match:
                    nonlocal token_found
                    token_found = match.group(1)
                    return  

        page.on("response", handle_response)
        page.goto("https://www.gov.ky/gazettes/gazettes")
        page.wait_for_timeout(10000)  # Wait 10 seconds for requests 

        browser.close()
        return token_found

years_id = {   
    2025: "EBEAC76BE72D429B8CB93DBC47CEB5BB",
    2024: "8EB09C3BE33647B8ACC41D11C912C2E4",
    2023: "28F6B30906024804B491A496BCF56078",
    2022: "13F51BAC20A048AFB91A15887614E669",
    2021: "13F51BAC20A048AFB91A15887614E669",
    2020: "13F51BAC20A048AFB91A15887614E669",
}

years_limit = {
    2022: {"gt": "20211231", "lt": "20230101"},
    2021: {"gt": "20201231", "lt": "20220101"},
    2020: {"gt": "20191231", "lt": "20210101"},
}

scraped = {   
    2025: 8,
    2024: 26,
    2023: 26,
    2022: 26,
    2021: 26,
    2020: 26,
}

# Unused
def get_year_ids():
    ids = []
    url = 'https://www.gov.ky/gazettes/pages/48.json'
    response = requests.get(url)
    content = response.json()
    body = content.get('base').get("slots").get('body')
    components = body.get('components')
    component_instances = content.get('base').get('componentInstances')
    for c in components:
        cat = component_instances.get(c).get("data").get("categoryFilters")
        if cat:
            id = cat[0].get("categories")[0]
            ids.append(id)

    return ids

def scrape_year(year=2025):
    """
    Scrapes gazette attachments from the Cayman Islands Gazette API for a given year.

    Args:
        year (int): The year for which to scrape gazettes. Defaults to 2025.

    Returns:
        List[str]: A list of attachment IDs corresponding to the gazette PDFs.
    """
    base_url = "https://www.gov.ky/content/published/api/v1.1/items"

    query = f"""((type eq "Publication") and (language eq "en-GB" or translatable eq "false") and ((taxonomies.categories.nodes.id eq "{years_id.get(year)}"))"""
    if year > 2022:
        query += ")"
    else:
        query += f""" and (fields.release_date gt "{years_limit.get(year).get('gt')}" AND fields.release_date lt "{years_limit.get(year).get('lt')}"))"""

    params = {
        "fields": "ALL",
        "orderBy": "fields.release_date:desc",
        "totalResults": "true",
        "channelToken": TOKEN,
        "q": query,
    }

    response = requests.get(base_url, params = params)
    gazettes = response.json()

    # Extract the ids from the json to get pdf
    attachments = []
    items = gazettes.get('items')
    for item in items:
        attachment = item.get('fields').get('attachment')[0].get('id')
        attachments.append(attachment)
    return attachments

def scrape(year):
    """
    Downloads and merges Cayman Islands Gazette PDFs for a given range of years.

    Args:
        year (int): The year for which to scrape gazettes. Defaults to 2025.

    Returns:
        BytesIO: The merged PDF.
    """
    attachments = scrape_year(year)
    file_path = os.path.join('data', f"gazettes-{year}.pdf")

    # If attachments have been scraped, return the scraped file
    if year in scraped and scraped[year] == len(attachments) and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return BytesIO(f.read())

    # From the ids, download the PDFs and combine
    merger = PdfMerger()
    for a in attachments:
        url = f'https://www.gov.ky/content/published/api/v1.1/items/{a}?channelToken={TOKEN}'
        response = requests.get(url)
        content = response.json()
        pdf_url = content.get('fields').get('native').get('links')[0].get('href')
        pdf_response = requests.get(pdf_url)
        if pdf_response.status_code == 200:
            pdf_file = BytesIO(pdf_response.content)
            merger.append(pdf_file)

    output_pdf = BytesIO()
    merger.write(output_pdf)
    merger.close()
    output_pdf.seek(0)

    return output_pdf
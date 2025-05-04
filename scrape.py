import requests
import re
import os
from PyPDF2 import PdfReader, PdfMerger 
from io import BytesIO
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

TOKEN = "3d887eb9d03345709d279836a8be130e"

years_id = {   
    2025: "EBEAC76BE72D429B8CB93DBC47CEB5BB",
    2024: "8EB09C3BE33647B8ACC41D11C912C2E4",
    2023: "28F6B30906024804B491A496BCF56078",
    2022: "13F51BAC20A048AFB91A15887614E669",
    2021: "13F51BAC20A048AFB91A15887614E669",
    2020: "13F51BAC20A048AFB91A15887614E669",
}

years_limit = {
    2023: {"gt": "20221231", "lt": "20240101"},
    2022: {"gt": "20211231", "lt": "20230101"},
    2021: {"gt": "20201231", "lt": "20220101"},
    2020: {"gt": "20191231", "lt": "20210101"},
}

scraped = {   
    2025: 9,
    2024: 29,
    2023: 26,
    2022: 24,
    2021: 26,
    2020: 26,
}

first_pages_by_year = {
    2020: [0, 170, 298, 418, 494, 570, 685, 754, 826, 895, 996, 1078, 1172, 1252, 1330, 1395, 1454, 1517, 1584, 1633, 1699, 1788, 1838, 1879, 1925, 2001],
    2021: [0, 152, 258, 368, 581, 656, 737, 819, 888, 946, 1030, 1092, 1174, 1227, 1301, 1366, 1470, 1555, 1608, 1659, 1717, 1775, 1822, 1869, 1951, 2004],
    2022: [0, 108, 219, 370, 450, 564, 632, 746, 810, 908, 973, 1035, 1112, 1185, 1241, 1297, 1358, 1413, 1473, 1516, 1595, 1646, 1700, 1757],
    2023: [0, 157, 285, 421, 495, 574, 674, 743, 811, 869, 958, 1035, 1106, 1168, 1230, 1296, 1361, 1419, 1488, 1543, 1616, 1661, 1722, 1779, 1830, 1896],
    2024: [0, 138, 243, 348, 444, 532, 605, 707, 763, 830, 896, 983, 1027, 1093, 1168, 1232, 1318, 1362, 1457, 1512, 1570, 1611, 1925, 1962, 2024, 2088],
    2025: [0, 51, 115, 168, 221, 294, 344, 429]
}

extra_years_id = {   
    2025: "04818F32F9C943C68DBB1D41846591FC",
    2024: "109A53AFBFB54FC3B480E5125D030511",
    2023: "1F76667E14EB465B962C5F143DD2119C"
}

def get_scraped_pdf_link(year):
    base_url = "https://vxgshoevqyuwt2kw.public.blob.vercel-storage.com/"
    if year <= 2019: # Scraped from archive
        return base_url + f"gazettes-archive-{year}.pdf"
    else: # Scraped from main page
        return base_url + f"gazettes-{year}.pdf"


def get_extraordinary_pdf_link(year):
    base_url = "https://vxgshoevqyuwt2kw.public.blob.vercel-storage.com/"
    if year <= 2022 and year >= 2004:
        return base_url + f"extraordinary-gazettes-archive-{year}.pdf"
    else:
        return base_url + f"extraordinary-gazettes-{year}.pdf"


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

# For future use (i.e. 2026)
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
    # Previous years have been scraped, so just return
    if (year <= 2024 and year >= 2004):
        f = requests.get(get_scraped_pdf_link(year))
        return BytesIO(f.content)

    if year == 2025:
        attachments = scrape_year(2025)
        l = len(attachments)
        offset = l - scraped[year]
        # If all 2025 attachments have been scraped and stored in the cloud, return the scraped file
        if offset == 0:
            f = requests.get(get_scraped_pdf_link(year))
            return BytesIO(f.content)

        merger = PdfMerger()
        attachments = attachments[:offset]

        # Else, download new files
        for a in attachments:
            url = f'https://www.gov.ky/content/published/api/v1.1/items/{a}?channelToken={TOKEN}'
            response = requests.get(url)
            content = response.json()
            pdf_url = content.get('fields').get('native').get('links')[0].get('href')
            pdf_response = requests.get(pdf_url)
            if pdf_response.status_code == 200:
                pdf_file = BytesIO(pdf_response.content)
                merger.append(pdf_file)
        
        # Append to scraped file
        f = requests.get(get_scraped_pdf_link(year))
        pdf_file = BytesIO(f.content)
        merger.append(pdf_file)

        output_pdf = BytesIO()
        merger.write(output_pdf)
        merger.close()
        output_pdf.seek(0)

        return output_pdf

# Not in use
def scrape_archive(year):
    """
    Downloads and merges Cayman Islands Gazette archived PDFs for a given year.

    Args:
        year (int): The year for which to scrape archived gazettes.

    Returns:
        BytesIO: The merged PDF.
    """
    merger = PdfMerger()
    base_url = "https://archives.gov.ky/sites/gazettes/www.gazettes.gov.ky/portal/"
    year_url = f"page/portal/gazhome/publications/gazettes/{year}.html"
    response = requests.get(base_url + year_url)
    soup = BeautifulSoup(response.text, "html.parser")  
    attachments = []   
    for link in soup.select("a[href$='.PDF']"):
        pdf_link = link['href'][15:]
        attachments.append(pdf_link)

    for a in set(attachments):
        pdf_response = requests.get(base_url + a)
        if pdf_response.status_code == 200:
            pdf_file = BytesIO(pdf_response.content)
            merger.append(pdf_file)

    output_pdf = BytesIO()
    merger.write(output_pdf)
    merger.close()
    output_pdf.seek(0)

    return output_pdf


def get_first_pages(year, latest_year=2025):
    """
    Get the start pages of each issue in a merged PDF.

    Args:
        year (str): The year of the merged PDF.

    Returns:
        start_pages: Array of start pages.
    """

    if year < latest_year:
        return first_pages_by_year.get(year)

    if year == latest_year and len(scrape_year(year)) == len(first_pages_by_year[year]):
        return first_pages_by_year.get(year)

    year_pdf = scrape(year)  
    reader = PdfReader(year_pdf)

    first_pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and 'CONTENTS' in text:
            first_pages.append(i)
    return first_pages

def search(term, start_year, end_year):
    """
    Search Cayman Islands Gazette PDFs for a given term.
    The term should be case-insensitive.

    Args:
        term (str): The search term.

    Returns:
        BytesIO: The merged PDF.
    """
    merger = PdfMerger() 

    for year in range(start_year, end_year + 1):
        print(f"Searching for {term} in {year}...")
        first_pages = get_first_pages(year)
        year_pdf = scrape(year)  
        reader = PdfReader(year_pdf)
        found_pages = []
        start_pages = []
        end_pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and term.lower() in text.lower():
                if not found_pages:
                    found_pages.append(i)

        for page in found_pages:
            # Find start and end page of an issue
            end_page = None
            for c in first_pages:
                if c <= page:
                    start_page = c
                else:
                    end_page = c
                    break

            # Append to merger PDF if a new issue contains the term
            if start_page not in start_pages:
                start_pages.append(start_page)
                # Append the range [start_page, end_page) (end exclusive)
                year_pdf.seek(0)  
                sub_reader = PdfReader(year_pdf)
                if end_page:
                    merger.append(year_pdf, pages = (start_page, end_page))
                else:
                    merger.append(year_pdf, pages = (start_page, len(sub_reader.pages)))

    output_pdf = BytesIO()
    merger.write(output_pdf)
    merger.close()
    output_pdf.seek(0)

    return output_pdf

def simple_search(term, start_year, end_year):
    """
    Search Cayman Islands Gazette PDFs for a given term.
    The term should be case-insensitive.

    Args:
        term (str): The search term.

    Returns:
        years_with_term: The years containing the term.
    """
    years_with_term = []
    term = term.lower()
    for year in range(start_year, end_year + 1):
        print(f"Searching for {term} in {year}...")
        year_pdf = scrape(year)  
        reader = PdfReader(year_pdf)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and term in text.lower():
                years_with_term.append(year)
                break

    return years_with_term

# Not in use
def scrape_extraordinary_archive(year):
    """
    Downloads and merges Cayman Islands Extraordinary Gazette archived PDFs for a given year.

    Args:
        year (int): The year for which to scrape archived gazettes.

    Returns:
        BytesIO: The merged PDF.
    """
    merger = PdfMerger()
    base_url = "https://archives.gov.ky/sites/gazettes/www.gazettes.gov.ky/portal/"
    year_url = f"page/portal/gazhome/publications/extraordinary-gazettes/{year}.html"
    response = requests.get(base_url + year_url)
    soup = BeautifulSoup(response.text, "html.parser")  
    attachments = []   
    for link in soup.select("a[href$='.PDF']"):
        pdf_link = link['href'][15:]
        attachments.append(pdf_link)

    for a in set(attachments):
        pdf_response = requests.get(base_url + a)
        if pdf_response.status_code == 200:
            pdf_file = BytesIO(pdf_response.content)
            merger.append(pdf_file)

    output_pdf = BytesIO()
    merger.write(output_pdf)
    merger.close()
    output_pdf.seek(0)

    return output_pdf


def scrape_extra_year(year=2025):
    """
    Scrapes extraordinary gazette attachments from the Cayman Islands Gazette API for a given year.

    Args:
        year (int): The year for which to scrape extra gazettes. Defaults to 2025.

    Returns:
        List[str]: A list of attachment IDs corresponding to the gazette PDFs.
    """
    base_url = "https://www.gov.ky/content/published/api/v1.1/items"

    query = f"""((type eq "Publication") and (language eq "en-GB" or translatable eq "false") and ((taxonomies.categories.nodes.id eq "{extra_years_id.get(year)}"))"""
    if year > 2023:
        query += ")"
    else:
        query += f""" and (fields.release_date gt "{years_limit.get(year).get('gt')}" AND fields.release_date lt "{years_limit.get(year).get('lt')}"))"""

    params = {
        "fields": "ALL",
        "orderBy": "fields.release_date:desc",
        "totalResults": "true",
        "channelToken": TOKEN,
        "q": query,
        "limit": 200,
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


def scrape_extraordinary(year):
    """
    Downloads and merges Cayman Islands Extraordinary Gazette PDFs for a given year.

    Args:
        year (int): The year for which to scrape extraordinary gazettes.

    Returns:
        BytesIO: The merged PDF.
    """
    # Previous years have been scraped, so just return
    if (year <= 2024 and year >= 2004):
        f = requests.get(get_extraordinary_pdf_link(year))
        return BytesIO(f.content)

    elif year == 2025:
        attachments = scrape_extra_year(year)
        l = len(attachments)
        offset = 37 # CHANGE HERE WHEN UPDATE
        # If all 2025 attachments have been scraped and stored in the cloud, return the scraped file
        if offset == 0:
            f = requests.get(get_extraordinary_pdf_link(year))
            return BytesIO(f.content)

        merger = PdfMerger()
        attachments = attachments[:offset]

        # Else, download new files
        for a in attachments:
            url = f'https://www.gov.ky/content/published/api/v1.1/items/{a}?channelToken={TOKEN}'
            response = requests.get(url)
            content = response.json()
            pdf_url = content.get('fields').get('native').get('links')[0].get('href')
            pdf_response = requests.get(pdf_url)
            if pdf_response.status_code == 200:
                pdf_file = BytesIO(pdf_response.content)
                merger.append(pdf_file)
        
        # Append to scraped file
        f = requests.get(get_scraped_pdf_link(year))
        pdf_file = BytesIO(f.content)
        merger.append(pdf_file)

        output_pdf = BytesIO()
        merger.write(output_pdf)
        merger.close()
        output_pdf.seek(0)

        return output_pdf
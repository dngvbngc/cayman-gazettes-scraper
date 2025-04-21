import requests
from PyPDF2 import PdfMerger 
from io import BytesIO

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

# Unused
def get_year_ids(token):
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

def scrape_year(token, year=2025):
    """
    Scrapes gazette attachments from the Cayman Islands Gazette API for a given year.
    Channel token must be collected manually by accessing the Gazette website.

    Args:
        token (str): The channel token for API authentication.
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
        "channelToken": token,
        "q": query,
    }

    response = requests.get(base_url, params = params)
    gazetts = response.json()

    # Extract the ids from the json to get pdf
    attachments = []
    items = gazetts.get('items')
    for item in items:
        attachment = item.get('fields').get('attachment')[0].get('id')
        attachments.append(attachment)
    return attachments

def scrape(token, year):
    """
    Downloads and merges Cayman Islands Gazette PDFs for a given range of years.

    Args:
        token (str): Channel token for authenticating API requests.
        start_year (int, optional): The starting year for scraping gazettes (inclusive). Defaults to 2020.
        end_year (int, optional): The ending year for scraping gazettes (inclusive). Defaults to 2025.

    Returns:
        BytesIO: The merged PDF.
    """
    attachments = scrape_year(token, year)
    merger = PdfMerger()

    # From the ids, download the PDFs and combine
    for a in attachments:
        url = f'https://www.gov.ky/content/published/api/v1.1/items/{a}?channelToken={token}'
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
import requests

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

# Scrape gazetts from Cayman Gazetts
# 2 sources: Gazett page & Archive page
# Collect channel token by manually accessing website

def scrape(token: str, year):
    # From the main Gazett page, request for gazetts
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

    if str(gazetts.get('hasMore')) == 'True':
        print('More gazetts to be found...')

    # Extract the slugs from the json and go to each associated page to get pdf
    slugs = []
    items = gazetts.get('items')
    for item in items:
        slug = item.get('slug')
        slugs.append(slug)
    print(slugs)

scrape('3d887eb9d03345709d279836a8be130e', 2021)

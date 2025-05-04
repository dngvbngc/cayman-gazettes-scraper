## How to maintain the site

1. Update token: If the channel token change, need to update `TOKEN` in `scrape.py`.

2. A new gazette is uploaded: If the server timeout, run the local application to retrieve the latest gazettes and replace it in `./data`. Also update `scraped` dictionary in `scrape.py`.

3. New year after 2025: Add year ID in `years_id` dictionary in `scrape.py`.

## How to improve the site

1. Faster search: Use regex to create a company corpus for each year, search the company corpus.

## How to run the local application

1. Fork the repository
2. Go to the repository in your terminal
3. Install virtualenv with `pip3 install virtualenv`
4. Create venv with `python3 -m venv .venv`
5. Activate venv with `source .venv/bin/activate`
6. Install requirements with `pip3 install -r requirements.txt`
7. (Optional) To install playwright, `playwright install`
8. Run the site via running `flask run`
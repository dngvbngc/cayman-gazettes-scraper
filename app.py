from flask import Flask, render_template, request, Response, send_file
from scrape import scrape, search, simple_search, scrape_archive, scrape_extraordinary

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    year = request.form.get('year')
    year = int(year) if year else 2025
    pdf_file = scrape(year)
    return send_file(pdf_file, as_attachment = True, download_name = f'gazettes-{year}.pdf', mimetype="application/pdf")

@app.route('/search-pdf', methods=['POST'])
def search_pdf():
    term = request.form.get('term')
    start_year = int(request.form.get('start-year'))
    end_year = int(request.form.get('end-year'))

    pdf_file = search(term, start_year, end_year)
    return send_file(pdf_file, as_attachment = True, download_name = f'gazettes-{term}.pdf', mimetype="application/pdf")

@app.route('/simple-search', methods=['POST'])
def simple_search_page():
    term = request.form.get('simple-search-term')
    start_year = int(request.form.get('simple-start-year'))
    end_year = int(request.form.get('simple-end-year'))
    years = simple_search(term, start_year, end_year)
    return render_template( 'simple-search.html', 
                            term = term, 
                            start_year = start_year,
                            end_year = end_year,
                            years = years)

@app.route('/scrape-archive-pdf', methods=['POST'])
def scrape_archive_pdf():
    year = int(request.form.get('archive-year'))
    pdf_file = scrape_archive(year)
    return send_file(pdf_file, as_attachment = True, download_name = f'gazettes-archive-{year}.pdf', mimetype="application/pdf")

@app.route('/scrape-extraordinary-pdf', methods=['POST'])
def scrape_extraordinary_pdf():
    year = int(request.form.get('extraordinary-year'))
    pdf_file = scrape_extraordinary(year)
    return send_file(pdf_file, as_attachment = True, download_name = f'extraordinary-gazettes-{year}.pdf', mimetype="application/pdf")

if __name__ == '__main__':
	app.run()

from flask import Flask, render_template, request, Response, send_file
from scrape import scrape, search, simple_search, scrape_archive, scrape_extraordinary
import bcrypt

app = Flask(__name__)

PASSWORD_HASH = b'$2b$12$uBSZXV7s2YjmwiY8yfiN5uuIKXZwUiI5f4NkhDANK1EkR5Nt3AH0W'
SALT = b'$2b$12$uBSZXV7s2YjmwiY8yfiN5u'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        code = request.form.get('code')
        byte_code = str.encode(code)
        if bcrypt.hashpw(byte_code, SALT) == PASSWORD_HASH:
	        return render_template('index.html')
        else:
            return '<p>Wrong access code</p>'

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

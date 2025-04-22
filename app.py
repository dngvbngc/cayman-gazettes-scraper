from flask import Flask, render_template, request, Response, send_file
from scrape import scrape

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

if __name__ == '__main__':
	app.run()

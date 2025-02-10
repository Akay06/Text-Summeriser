from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from time import strftime
import openai
import os
import logging
from werkzeug.utils import secure_filename
from groq import Groq
import markdown


#client = google.cloud.logging.Client()
#client.setup_logging()

app = Flask(__name__)
summaries = {}

#logging.basicConfig(level=logging.INFO)

#BUCKET_NAME = 'PROD_BUCKET_NAME'

#def getOpenaiSecret():
#    client = secretmanager.SecretManagerServiceClient()
#    return client.access_secret_version(request={"name": "projects/1018379038222/secrets/OPENAI_API_KEY/versions/1"}).payload.data.decode("UTF-8")

API_KEY = os.environ.get('GROQ_API_KEY')
client = Groq(
    api_key=API_KEY,
)
MAX_TOKENS = 4000

# Configure Google Cloud Storage
#storage_client = storage.Client()
#bucket_name = os.environ.get(BUCKET_NAME)  # Add the bucket name here 
#bucket = storage_client.bucket(bucket_name)

def upload_to_gcs(file):
    if file:
        filename = secure_filename(file.filename)
        blob = bucket.blob(filename)
        blob.upload_from_string(file.read(), content_type=file.content_type)
        return filename

@app.route('/')
def index():
    logging.info('Inside ' + index.__name__ + '()')
    try:
        return render_template('index1.html')
    except ValueError:
        logging.exception(index.__name__ + '(): ' + ValueError)

@app.route('/api/upload_and_summarize', methods=['POST'])
def upload_and_summarize():
    logging.info('Inside ' + upload_and_summarize.__name__+ '()')
    try:
        if 'file' in request.files:
            pdf_file = request.files['file']
            if pdf_file.filename != '':

                #gcs_filename = upload_to_gcs(pdf_file)
                
                # Extract text from the uploaded PDF file
                content = extract_text_from_pdf(pdf_file)
    
                # Generate summary from the extracted text
                summary = generate_summary(content)
                summary_id = len(summaries) + 1
                summaries[summary_id] = summary
    
                return jsonify({'summary_id': summary_id, 'filename_uploaded': pdf_file.filename})
        
        elif 'text' in request.json:
            text = request.json['text']
            if text:
                # Generate summary from the input text
                summary = generate_summary(text)
                summary_id = len(summaries) + 1
                summaries[summary_id] = summary
    
                return jsonify({'summary_id': summary_id})
        
        return jsonify({'error': 'Invalid input'})
    except ValueError:
        logging.exception(upload_and_summarize.__name__ + '(): ' + ValueError)

@app.route('/summary/<int:summary_id>')
def show_summary(summary_id):
    logging.info('Inside ' + show_summary.__name__+ '()')
    try:
        summary = summaries.get(summary_id)
        if summary:
            return render_template('summary1.html', summary=summary)
        else:
            return "Summary not found."
    except ValueError:
        logging.exception(show_summary.__name__ + '(): ' + 'summary_id ' + summary_id + ' ' + ValueError)

def extract_text_from_pdf(pdf_file):
    logging.info('Inside ' + extract_text_from_pdf.__name__+ '()')
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text
    except ValueError:
        logging.exception(extract_text_from_pdf.__name__ + '(): ' + ValueError)

def generate_summary(content):
    logging.info('Inside ' + generate_summary.__name__+ '()')
    try:
        chunks = [content[i:i + MAX_TOKENS] for i in range(0, len(content), MAX_TOKENS)]
        summaries = []
        for chunk in chunks:
            prompt = f"Summarize the following text:\n\n{chunk}"
            response = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                        temperature=0.9,
                        max_completion_tokens=1024,
                        top_p=1,
)
            summary = response.choices[0].message.content
            summary = markdown.markdown(summary)
            summaries.append(f"""{summary}""")
    
        return '\n'.join(summaries)
    except ValueError:
        logging.exception(generate_summary.__name__ + '(): ' + ValueError)

if __name__ == '__main__':
    app.run(debug=True)

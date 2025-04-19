import os
import json
import tempfile
import traceback
from flask import Flask, render_template, request, flash, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from medical_history import (
    setup_env, extract_text_from_document,
    extract_basic_info_from_text, extract_medical_history_from_text,
    get_personalized_medicine_details, format_personalized_info,
    Groq
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_json_parse(text, groq_client, model, retry_count=3):
    for attempt in range(retry_count):
        try:
            if isinstance(text, dict):
                return text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            prompt = f"""
            Extract structured information from the following text as a valid JSON object.
            If you cannot parse certain fields, use null or empty strings rather than malformed JSON.
            Always return a complete, valid JSON object.
            
            Text to parse:
            {text[:2000]}
            """
            response = groq_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            result = response.choices[0].message.content
            import re
            json_match = re.search(r'({[\s\S]*})', result)
            if json_match:
                result = json_match.group(1)
            return json.loads(result)
        except Exception as e:
            app.logger.error(f"JSON parsing attempt {attempt+1} failed: {str(e)}")
            if attempt == retry_count - 1:
                return {"error": "Could not parse response", "raw_text": text[:500] + "..."}
    return {"error": "Failed to parse after multiple attempts"}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not setup_env():
            flash("Server configuration error. Please contact administrator.")
            return render_template('index.html')
        
        try:
            groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            model = os.getenv('MODEL', 'llama3-70b-8192')
        except Exception as e:
            flash(f"Error initializing AI service: {str(e)}")
            return render_template('index.html')

        if 'medicine_file' not in request.files or 'medical_history_file' not in request.files:
            flash('Missing file uploads')
            return render_template('index.html')
        
        medicine_file = request.files['medicine_file']
        history_file = request.files['medical_history_file']

        if medicine_file.filename == '' or history_file.filename == '':
            flash('No selected files')
            return render_template('index.html')

        if not (allowed_file(medicine_file.filename) and allowed_file(history_file.filename)):
            flash('Invalid file types. Allowed: png, jpg, jpeg, pdf')
            return render_template('index.html')

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                medicine_path = os.path.join(tmp_dir, secure_filename(medicine_file.filename))
                medicine_file.save(medicine_path)
                medicine_text = extract_text_from_document(medicine_path)
                if not medicine_text:
                    flash("Could not extract text from medicine file")
                    return render_template('index.html')

                history_path = os.path.join(tmp_dir, secure_filename(history_file.filename))
                history_file.save(history_path)
                history_text = extract_text_from_document(history_path)
                if not history_text:
                    flash("Could not extract text from medical history file")
                    return render_template('index.html')

                medicine_info = extract_basic_info_from_text(medicine_text, groq_client, model)
                if isinstance(medicine_info, str):
                    medicine_info = safe_json_parse(medicine_info, groq_client, model)

                medical_history = extract_medical_history_from_text(history_text, groq_client, model)
                if isinstance(medical_history, str):
                    medical_history = safe_json_parse(medical_history, groq_client, model)

                personalized_info = get_personalized_medicine_details(medicine_info, medical_history, groq_client, model)
                if isinstance(personalized_info, str):
                    personalized_info = safe_json_parse(personalized_info, groq_client, model)

                report = format_personalized_info(medicine_info, medical_history, personalized_info)
                html_report = report.replace('\n', '<br>').replace(' ', '&nbsp;')

                app.logger.info(f"Successfully processed files: {medicine_file.filename} and {history_file.filename}")
                return render_template('index.html', report=html_report)

        except Exception as e:
            error_details = traceback.format_exc()
            app.logger.error(f"Processing error: {str(e)}\n{error_details}")
            flash(f'Error processing files: {str(e)}. Please try again.')
            return render_template('index.html')

    return render_template('index.html', report=None)

@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum file size is 16MB.")
    return render_template('index.html'), 413

@app.errorhandler(500)
def server_error(e):
    flash("Server error occurred. Please try again later.")
    return render_template('index.html'), 500

if __name__ == '__main__':
    if not setup_env():
        print("Please configure your .env file first")
    else:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        app.run(debug=True)
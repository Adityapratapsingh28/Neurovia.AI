import os
from flask import Flask, request, render_template, send_from_directory
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the model
# Update the path to your model file
model = load_model(r"D:\neurovia-main\Models\tuberculosis_classifier2.h5")

# Define class names for tuberculosis dataset
class_names = ['normal', 'tuberculosis']

def predict_tuberculosis(img_path):
    # Load and preprocess the image
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize to match your model's input size (adjust if needed)
    img_resized = cv2.resize(img, (224, 224))  # Update with your model's input size
    
    # Normalize pixel values (adjust if your model was trained differently)
    img_array = img_resized / 255.0
    
    # Reshape for model input
    img_array = np.expand_dims(img_array, axis=0)

    # Make prediction
    predictions = model.predict(img_array)
    
    # Check if prediction output is a single value (binary) or array (multi-class)
    if len(predictions.shape) > 1 and predictions.shape[1] > 1:
        # Multi-class scenario
        predicted_class_index = np.argmax(predictions[0])
        confidence = round(100 * np.max(predictions[0]), 2)
    else:
        # Binary classification scenario
        pred_value = predictions[0][0]
        predicted_class_index = 1 if pred_value > 0.5 else 0
        confidence = round(100 * (pred_value if pred_value > 0.5 else 1 - pred_value), 2)
    
    predicted_class = class_names[predicted_class_index]
    
    return predicted_class, confidence

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', message='No file part')
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', message='No selected file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            predicted_class, confidence = predict_tuberculosis(file_path)
            return render_template('result.html', 
                                  filename=filename, 
                                  prediction=predicted_class, 
                                  confidence=confidence)
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=3021)
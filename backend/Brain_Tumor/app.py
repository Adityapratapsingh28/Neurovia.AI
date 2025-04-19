import os
from flask import Flask, request, render_template, send_from_directory
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import matplotlib.pyplot as plt
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input
import tensorflow as tf
from werkzeug.utils import secure_filename
import base64
from io import BytesIO

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the model
model = load_model(r"D:\neurovia-main\Models\model_bone_fracture.h5")

# Define class names
class_names = ['Glioma Tumor', 'Meningioma Tumor', 'No Tumor', 'Pituitary Tumor']

def generate_heatmap(img_path, model, last_conv_layer_name='conv2d_2'):
    # Load and preprocess the image
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (150, 150))
    img_array = img_to_array(img_resized)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0

    # Get the last convolutional layer
    last_conv_layer = model.get_layer(last_conv_layer_name)
    
    # Create a model that maps the input image to the activations of the last conv layer
    conv_model = Model(model.inputs, last_conv_layer.output)
    
    # Create a model that maps the activations of the last conv layer to the final class predictions
    classifier_input = Input(shape=last_conv_layer.output.shape[1:])
    x = classifier_input
    for layer in model.layers[model.layers.index(last_conv_layer)+1:]:
        x = layer(x)
    classifier_model = Model(classifier_input, x)
    
    # Compute gradient of top predicted class
    with tf.GradientTape() as tape:
        # Compute activations of last conv layer and make the tape watch it
        conv_output = conv_model(img_array)
        tape.watch(conv_output)
        # Compute class predictions
        predictions = classifier_model(conv_output)
        top_pred_index = tf.argmax(predictions[0])
        top_class_channel = predictions[:, top_pred_index]
    
    # Compute gradients
    grads = tape.gradient(top_class_channel, conv_output)
    
    # Pool gradients over all the axes leaving out the channel dimension
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Multiply each channel in the feature map array by its importance
    conv_output = conv_output.numpy()[0]
    pooled_grads = pooled_grads.numpy()
    for i in range(pooled_grads.shape[-1]):
        conv_output[:, :, i] *= pooled_grads[i]
    
    # Create heatmap
    heatmap = np.mean(conv_output, axis=-1)
    heatmap = np.maximum(heatmap, 0)  # ReLU
    heatmap /= np.max(heatmap)  # Normalize
    
    # Resize heatmap to match original image size
    heatmap = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heatmap = np.uint8(255 * heatmap)
    
    # Apply colormap
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    
    # Superimpose heatmap on original image
    superimposed_img = heatmap * 0.4 + img * 0.6
    superimposed_img = np.clip(superimposed_img, 0, 255).astype('uint8')
    
    return superimposed_img, heatmap

def predict_tumor(img_path):
    # Load and preprocess the image
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (150, 150))
    img_array = np.array(img_resized)
    img_array = img_array.reshape(1, 150, 150, 3)
    
    # Make prediction
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions[0])
    predicted_class = class_names[predicted_class_index]
    confidence = round(100 * np.max(predictions[0]), 2)
    
    # Generate heatmap
    heatmap_img, _ = generate_heatmap(img_path, model)
    
    # Convert heatmap to base64 for HTML display
    buffered = BytesIO()
    plt.imsave(buffered, heatmap_img, format='png')
    heatmap_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return predicted_class, confidence, heatmap_base64

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
            predicted_class, confidence, heatmap = predict_tumor(file_path)
            return render_template('result.html', 
                                 filename=filename, 
                                 prediction=predicted_class, 
                                 confidence=confidence,
                                 heatmap=heatmap)
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=3019)
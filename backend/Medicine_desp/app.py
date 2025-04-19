from flask import Flask, render_template, request, jsonify
import os
import easyocr
from spellchecker import SpellChecker
from groq import Groq
import json
import re
from datetime import datetime
import logging
from dotenv import load_dotenv
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
def setup_env():
    """
    Create and load .env file for API keys and settings
    """
    # Check if .env file exists, if not create it
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write('# Groq API Key\nGROQ_API_KEY=your-groq-api-key-here\n\n# Model to use\nMODEL=llama3-70b-8192\n')
        logger.info("Created .env file. Please update with your actual GROQ API key.")
        return False
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if the API key is set to the default value
    if os.getenv('GROQ_API_KEY') == 'your-groq-api-key-here':
        logger.warning("Please update the GROQ_API_KEY in the .env file with your actual API key.")
        return False
    
    return True

# Initialize Groq client and other components
def initialize_components():
    env_loaded = setup_env()
    if not env_loaded:
        raise Exception("Please update the .env file with your API key and run again.")
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('MODEL', 'llama3-70b-8192')
    
    return Groq(api_key=groq_api_key), model

groq_client, model = initialize_components()

def extract_text_from_document(image_path):
    """
    Extract text from a document image with spelling correction
    """
    logger.info("Initializing OCR engine...")
    reader = easyocr.Reader(['en'], gpu=False)
    spell = SpellChecker()
    
    logger.info(f"Reading image from: {image_path}")
    results = reader.readtext(image_path)
    
    logger.info("Extracting and correcting text...")
    extracted_text = ""
    
    for detection in results:
        text = detection[1]
        confidence = detection[2]
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            if word.isalpha():
                corrected_word = spell.correction(word)
                if corrected_word:
                    corrected_words.append(corrected_word)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        corrected_text = " ".join(corrected_words)
        extracted_text += corrected_text + " "
    
    return extracted_text.strip()

def extract_basic_info_from_text(text):
    """
    Extract only basic medicine information from the OCR text
    """
    logger.info("Extracting basic medicine information from the OCR text...")
    
    extraction_prompt = f"""
    You are a professional pharmacist with expertise in medicine analysis. 
    Analyze the following text extracted from a medicine package and extract ONLY the following basic information:
    
    {text}
    
    Please provide the following information in a JSON format:
    
    1. Medicine Name
       - Brand Name
       - Generic Name
    2. Composition (active ingredients and their strength)
    3. Manufacturer Information (name and address)
    4. Manufacturing Date
    5. Expiry Date
    
    IMPORTANT: ONLY include information that is explicitly mentioned in the text. 
    If any information is not available in the text, mark it as "Not found in the provided text".
    
    Return ONLY the JSON object with no additional text or explanations.
    """
    
    try:
        extraction_response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You extract basic medicine information from OCR text and return it in JSON format."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=1024
        )
        
        extraction_result = extraction_response.choices[0].message.content
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', extraction_result)
        if json_match:
            extraction_result = json_match.group(1)
        
        try:
            return json.loads(extraction_result)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from initial extraction")
            return {"error": "Failed to parse basic medicine information", "raw_response": extraction_result}
    
    except Exception as e:
        logger.error(f"Error while extracting basic info: {str(e)}")
        return {"error": str(e)}

def get_medicine_details_from_llm(basic_info):
    """
    Use the LLM's knowledge to provide detailed information about the medicine
    """
    logger.info("Getting comprehensive medicine details from LLM knowledge...")
    
    try:
        medicine_name = basic_info.get('Medicine Name', {})
        brand_name = medicine_name.get('Brand Name', 'Unknown')
        generic_name = medicine_name.get('Generic Name', 'Unknown')
        
        composition = basic_info.get('Composition', 'Unknown')
        if isinstance(composition, dict):
            active_ingredient = composition.get('Active Ingredient', 'Unknown')
            strength = composition.get('Strength', 'Unknown')
            composition_str = f"{active_ingredient} {strength}"
        else:
            composition_str = str(composition)
    except Exception as e:
        logger.warning(f"Error extracting medicine identifiers: {str(e)}")
        brand_name = "Unknown"
        generic_name = "Unknown"
        composition_str = "Unknown"
    
    llm_knowledge_prompt = f"""
    You are a pharmaceutical expert with comprehensive knowledge about medications.
    
    Based on the following medicine identification:
    - Brand Name: {brand_name}
    - Generic Name: {generic_name}
    - Composition: {composition_str}
    
    Provide the following information about this medicine using your own knowledge (not limited to any text):
    
    1. Description of Medicine (brief overview of what this medicine is and its class)
    
    2. Storage Instructions (general storage recommendations)
    
    3. Usage Instructions/Indications (what conditions this medicine treats)
    
    4. Warnings/Cautions (important safety information)
    
    5. Side Effects (common and serious)
    
    6. Mandatory to give Dosage Information - Please be very specific with:
       - Daily schedule (how many tablets to take in morning, afternoon, evening)
       - Whether to take before or after meals
       - Typical duration of treatment
       - Dosage adjustments for special populations (elderly, kidney issues, etc.)
    
    7. Dietary Recommendations:
       - Foods to avoid while taking this medicine
       - Foods that may enhance or reduce effectiveness
       - Dietary restrictions if any
    
    8. Drug Interactions (important interactions with other medications)
    
    IMPORTANT: Use your pre-trained knowledge about pharmaceuticals to provide accurate, detailed information.
    DO NOT respond with "Not found" or similar phrases - provide the best information you have for each category.
    If the medicine identification is unclear, make your best judgment based on the generic name.
    
    Return ONLY a JSON object with these fields, providing comprehensive information for each.
    """
    
    try:
        llm_response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a pharmaceutical expert providing detailed medicine information from your knowledge."},
                {"role": "user", "content": llm_knowledge_prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        
        llm_result = llm_response.choices[0].message.content
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', llm_result)
        if json_match:
            llm_result = json_match.group(1)
        
        try:
            return json.loads(llm_result)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from LLM knowledge request")
            return {"error": "Failed to parse medicine details", "raw_response": llm_result}
    
    except Exception as e:
        logger.error(f"Error while getting medicine details from LLM: {str(e)}")
        return {"error": str(e)}

def combine_medicine_information(basic_info, llm_details):
    """
    Combine OCR-extracted basic info with LLM-provided detailed info
    """
    logger.info("Combining OCR-extracted info with LLM-provided details...")
    
    combined_info = {
        "Medicine Name": basic_info.get("Medicine Name", {}),
        "Composition": basic_info.get("Composition", "Not found"),
        "Manufacturer Information": basic_info.get("Manufacturer Information", "Not found"),
        "Manufacturing Date": basic_info.get("Manufacturing Date", "Not found"),
        "Expiry Date": basic_info.get("Expiry Date", "Not found"),
        
        "Description": llm_details.get("Description of Medicine", "Not provided"),
        "Storage Instructions": llm_details.get("Storage Instructions", "Not provided"),
        "Usage Instructions": llm_details.get("Usage Instructions/Indications", "Not provided"),
        "Warnings/Cautions": llm_details.get("Warnings/Cautions", "Not provided"),
        "Side Effects": llm_details.get("Side Effects", "Not provided"),
        "Dosage Information": llm_details.get("Dosage Information", "Not provided"),
        "Dietary Recommendations": llm_details.get("Dietary Recommendations", "Not provided"),
        "Drug Interactions": llm_details.get("Drug Interactions", "Not provided")
    }
    
    return combined_info

def handle_chat_message(user_message, medicine_info):
    """
    Handle chatbot messages using the medicine information
    """
    try:
        medicine_name = medicine_info.get('Medicine Name', {})
        brand_name = medicine_name.get('Brand Name', 'Unknown')
        generic_name = medicine_name.get('Generic Name', 'Unknown')
        composition = medicine_info.get('Composition', 'Unknown')
    except (AttributeError, TypeError):
        brand_name = "Unknown"
        generic_name = "Unknown"
        composition = "Unknown"
    
    chat_prompt = f"""
    You are MedBot, an AI assistant specialized in pharmaceutical advice and you should give answer related to health and medication only.
    You have information about the following medicine:
    
    - Brand Name: {brand_name}
    - Generic Name: {generic_name}
    - Composition: {composition}
    
    Additional information from the analysis:
    - Description: {medicine_info.get('Description', 'Not provided')}
    - Usage Instructions: {medicine_info.get('Usage Instructions', 'Not provided')}
    - Side Effects: {medicine_info.get('Side Effects', 'Not provided')}
    - Dosage Information: {medicine_info.get('Dosage Information', 'Not provided')}
    - Warnings/Cautions: {medicine_info.get('Warnings/Cautions', 'Not provided')}
    - Drug Interactions: {medicine_info.get('Drug Interactions', 'Not provided')}
    - Dietary Recommendations: {medicine_info.get('Dietary Recommendations', 'Not provided')}
    
    The user asked: "{user_message}"
    
    Please provide a helpful, accurate response based on the medicine information above.
    If the question is not related to this medicine, you can provide general pharmaceutical advice.
    Always include a disclaimer that you're an AI assistant and not a licensed healthcare professional.
    Advise consulting with a doctor or pharmacist for personalized medical advice.
    """
    
    try:
        chat_response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a pharmaceutical expert providing helpful, accurate information."},
                {"role": "user", "content": chat_prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        
        return chat_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in chatbot: {str(e)}")
        return "Sorry, I encountered an error while processing your question. Please try again."

# Flask Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, image_file.filename)
        image_file.save(image_path)
        
        # Extract text from image
        extracted_text = extract_text_from_document(image_path)
        
        # Step 1: Extract basic info from OCR text
        basic_info = extract_basic_info_from_text(extracted_text)
        
        if 'error' in basic_info:
            return jsonify(basic_info), 500
        
        # Step 2: Get detailed medicine information from LLM knowledge
        llm_details = get_medicine_details_from_llm(basic_info)
        
        if 'error' in llm_details:
            return jsonify(llm_details), 500
        
        # Step 3: Combine both sources of information
        combined_info = combine_medicine_information(basic_info, llm_details)
        
        # Clean up temporary file
        os.remove(image_path)
        os.rmdir(temp_dir)
        
        return jsonify(combined_info)
    
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    medicine_info = data.get('medicine_info', {})
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        response = handle_chat_message(user_message, medicine_info)
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Move index.html to templates directory
    if os.path.exists('index.html'):
        os.rename('index.html', 'templates/index.html')
    elif not os.path.exists('templates/index.html'):
        raise FileNotFoundError("index.html not found")
    
    # Run the Flask app
    app.run(debug=True, port=5000)
import os
import easyocr
import cv2
from spellchecker import SpellChecker
from groq import Groq
import json
import re
from datetime import datetime
import logging
from dotenv import load_dotenv
import pymupdf as fitz  # Explicitly use pymupdf to avoid conflicts
import tempfile
from PIL import Image
import numpy as np
import pathlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_env():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write('# Groq API Key\nGROQ_API_KEY=your-groq-api-key-here\n\n# Model to use\nMODEL=llama3-70b-8192\n')
        logger.info("Created .env file. Please update with your actual GROQ API key.")
        return False
    
    load_dotenv()
    if os.getenv('GROQ_API_KEY') == 'your-groq-api-key-here':
        logger.warning("Please update the GROQ_API_KEY in the .env file with your actual API key.")
        return False
    return True

def extract_text_from_pdf(pdf_path):
    logger.info(f"Extracting text from PDF: {pdf_path}")
    extracted_text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            extracted_text += page_text + "\n\n"
            if len(page_text.strip()) < 100:
                logger.info(f"Page {page_num+1} has minimal text, extracting images for OCR...")
                image_list = page.get_images(full=True)
                if image_list:
                    with tempfile.TemporaryDirectory() as tmpdirname:
                        for img_index, img in enumerate(image_list):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            img_filename = os.path.join(tmpdirname, f"page_{page_num}_img_{img_index}.png")
                            with open(img_filename, "wb") as img_file:
                                img_file.write(image_bytes)
                            img_text = extract_text_from_image(img_filename)
                            extracted_text += f"\n\nImage {img_index+1} OCR Text:\n{img_text}\n"
        doc.close()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return f"Error extracting text: {str(e)}"
    return extracted_text.strip()

def extract_text_from_image(image_path):
    logger.info(f"Extracting text from image: {image_path}")
    reader = easyocr.Reader(['en'], gpu=False)
    spell = SpellChecker()
    try:
        results = reader.readtext(image_path)
        extracted_text = ""
        for detection in results:
            text = detection[1]
            confidence = detection[2]
            if confidence < 0.5:
                continue
            words = text.split()
            corrected_words = []
            for word in words:
                if word.isalpha() and len(word) > 2:
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
    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")
        return f"OCR Error: {str(e)}"

def extract_text_from_document(document_path):
    file_extension = pathlib.Path(document_path).suffix.lower()
    if file_extension == '.pdf':
        return extract_text_from_pdf(document_path)
    elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp']:
        return extract_text_from_image(document_path)
    else:
        logger.error(f"Unsupported file format: {file_extension}")
        return f"Error: Unsupported file format {file_extension}. Please provide a PDF or image file."

def extract_medical_history_from_text(text, groq_client, model):
    logger.info("Extracting medical history information from the text...")
    extraction_prompt = f"""
    You are a medical specialist with expertise in analyzing medical reports and histories.
    Analyze the following text extracted from a medical history document:
    
    {text}
    
    Please extract and provide the following information in a JSON format:
    
    1. Patient Information
       - Name (if available)
       - Age (if available)
       - Gender (if available)
       - Weight (if available)
       - Height (if available)
    
    2. Medical Conditions (list all conditions mentioned)
       - Current conditions
       - Past conditions
    
    3. Laboratory Test Results (include all test parameters with values and normal ranges)
    
    4. Vital Signs (BP, pulse, etc. if available)
    
    5. Allergies (medicines, foods, or other substances)
    
    6. Current Medications (if mentioned)
    
    7. Past Surgeries or Procedures
    
    8. Family Medical History (if mentioned)
    
    9. Lifestyle Factors (smoking, alcohol, exercise habits if mentioned)
    
    IMPORTANT: ONLY include information that is explicitly mentioned in the text.
    If any information is not available in the text, mark it as "Not found in the provided text".
    
    Return ONLY the JSON object with no additional text or explanations.
    """
    try:
        extraction_response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You extract medical history information from text and return it in JSON format."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=1024
        )
        extraction_result = extraction_response.choices[0].message.content
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', extraction_result)
        if json_match:
            extraction_result = json_match.group(1)
        return json.loads(extraction_result)
    except Exception as e:
        logger.error(f"Error while extracting medical history: {str(e)}")
        return {"error": str(e)}

def extract_basic_info_from_text(text, groq_client, model):
    logger.info("Extracting basic medicine information from the text...")
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
                {"role": "system", "content": "You extract basic medicine information from text and return it in JSON format."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.2,
            max_tokens=1024
        )
        extraction_result = extraction_response.choices[0].message.content
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', extraction_result)
        if json_match:
            extraction_result = json_match.group(1)
        return json.loads(extraction_result)
    except Exception as e:
        logger.error(f"Error while extracting basic info: {str(e)}")
        return {"error": str(e)}

def get_personalized_medicine_details(basic_info, medical_history, groq_client, model):
    logger.info("Getting personalized medicine recommendations based on patient history...")
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
    
    serialized_history = json.dumps(medical_history, indent=2)
    personalized_prompt = f"""
    You are a specialized medical AI consultant with expertise in personalized medicine.
    
    You have been given:
    1. Information about a medication:
       - Brand Name: {brand_name}
       - Generic Name: {generic_name}
       - Composition: {composition_str}
    
    2. A patient's medical history details:
    {serialized_history}
    
    Based on the medication information and the patient's medical history, provide a PERSONALIZED analysis with the following information:
    
    1. Description of Medicine (brief overview of what this medicine is and its class)
    
    2. Storage Instructions (general storage recommendations)
    
    3. Personalized Usage Instructions/Indications
       - How this medicine relates to the patient's specific medical conditions
       - Whether this medicine is appropriate given their history
       - Any special considerations given their specific medical profile
    
    4. Personalized Warnings/Cautions
       - Specific safety concerns based on this patient's medical history, current medications, or conditions
       - Any contraindications or warnings specific to their profile
    
    5. Personalized Side Effects Monitoring
       - Side effects this specific patient should watch for given their medical history
       - How these side effects might interact with their existing conditions
    
    6. Personalized Dosage Information
       - Recommendations for dosage adjustments based on patient's profile (age, weight, conditions)
       - Daily schedule customized to their needs and current medication regimen
       - Whether to take before or after meals based on their specific situation
       - Duration considerations based on their conditions
    
    7. Personalized Dietary Recommendations
       - Foods to avoid considering both the medicine and their medical conditions
       - Foods that may be beneficial given their health profile
       - Dietary modifications that could enhance treatment outcomes
    
    8. Personalized Drug Interactions
       - Potential interactions with their current medications
       - How to manage their medication schedule to minimize interactions
    
    9. Personalized Recovery/Management Plan
       - Suggestions for lifestyle modifications to enhance medicine effectiveness
       - Monitoring recommendations specific to their conditions
       - Recovery timeline expectations based on their specific health profile
    
    IMPORTANT: For each section, clearly explain WHY these recommendations are personalized for this specific patient based on their medical history.
    Be specific about how their particular conditions, test results, or health factors inform your recommendations.
    
    If any information is insufficient to make personalized recommendations in a particular section, explicitly state what additional information would be needed.
    
    Return ONLY a JSON object with these fields, providing comprehensive information for each.
    """
    try:
        personalized_response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a medical AI providing personalized medicine information based on patient history."},
                {"role": "user", "content": personalized_prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        personalized_result = personalized_response.choices[0].message.content
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', personalized_result)
        if json_match:
            personalized_result = json_match.group(1)
        return json.loads(personalized_result)
    except Exception as e:
        logger.error(f"Error while getting personalized medicine details: {str(e)}")
        return {"error": str(e)}

def format_personalized_info(medicine_info, medical_history, personalized_info):
    try:
        medicine_name = medicine_info.get('Medicine Name', {})
        brand_name = medicine_name.get('Brand Name', 'Not found')
        generic_name = medicine_name.get('Generic Name', 'Not found')
        patient_info = medical_history.get('Patient Information', {})
        patient_name = patient_info.get('Name', 'Patient')
        patient_age = patient_info.get('Age', 'Not found')
        patient_gender = patient_info.get('Gender', 'Not found')
    except (AttributeError, TypeError):
        brand_name = "Not found"
        generic_name = "Not found"
        patient_name = "Patient"
        patient_age = "Not found"
        patient_gender = "Not found"
        
    formatted = f"""
=================================================
           PERSONALIZED MEDICINE REPORT
=================================================

PATIENT: {patient_name} (Age: {patient_age}, Gender: {patient_gender})
DATE: {datetime.now().strftime("%B %d, %Y")}

-------- MEDICINE INFORMATION --------

MEDICINE NAME:
  Brand Name: {brand_name}
  Generic Name: {generic_name}

COMPOSITION:
  {medicine_info.get('Composition', 'Not found')}

MANUFACTURER:
  {medicine_info.get('Manufacturer Information', 'Not found')}

DATES:
  Manufacturing Date: {medicine_info.get('Manufacturing Date', 'Not found')}
  Expiry Date: {medicine_info.get('Expiry Date', 'Not found')}

-------- PERSONALIZED MEDICINE ANALYSIS --------

DESCRIPTION:
  {personalized_info.get('Description of Medicine', 'Not provided')}

STORAGE INSTRUCTIONS:
  {personalized_info.get('Storage Instructions', 'Not provided')}

PERSONALIZED USAGE INSTRUCTIONS:
  {personalized_info.get('Personalized Usage Instructions/Indications', 'Not provided')}

PERSONALIZED WARNINGS/CAUTIONS:
  {personalized_info.get('Personalized Warnings/Cautions', 'Not provided')}

PERSONALIZED SIDE EFFECTS MONITORING:
  {personalized_info.get('Personalized Side Effects Monitoring', 'Not provided')}

PERSONALIZED DOSAGE INFORMATION:
  {personalized_info.get('Personalized Dosage Information', 'Not provided')}

PERSONALIZED DIETARY RECOMMENDATIONS:
  {personalized_info.get('Personalized Dietary Recommendations', 'Not provided')}

PERSONALIZED DRUG INTERACTIONS:
  {personalized_info.get('Personalized Drug Interactions', 'Not provided')}

PERSONALIZED RECOVERY/MANAGEMENT PLAN:
  {personalized_info.get('Personalized Recovery/Management Plan', 'Not provided')}

=================================================
DISCLAIMER: This personalized analysis is provided for informational purposes only.
Always consult with your healthcare provider before making any changes to your
medication regimen or treatment plan.
=================================================
"""
    return formatted
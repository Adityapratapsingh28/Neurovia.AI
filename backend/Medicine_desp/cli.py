import os
import easyocr
import cv2
import argparse
from spellchecker import SpellChecker
from groq import Groq
import json
import re
from datetime import datetime
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def extract_text_from_document(image_path):
    """
    Extract text from a document image with spelling correction
    
    Args:
        image_path (str): Path to the document image
        
    Returns:
        str: Extracted and corrected text
    """
    # Initialize the OCR reader
    logger.info("Initializing OCR engine...")
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Initialize spell checker
    spell = SpellChecker()
    
    # Read the image
    logger.info(f"Reading image from: {image_path}")
    results = reader.readtext(image_path)
    
    # Extract and correct text
    logger.info("Extracting and correcting text...")
    extracted_text = ""
    
    for detection in results:
        text = detection[1]
        confidence = detection[2]
        
        # Split text into words for spell checking
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Only apply spell correction to alphabetic words
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

def save_text_to_file(text, output_file="extracted_text.txt"):
    """Save extracted text to a file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Text saved to '{output_file}'")
    return output_file

def extract_basic_info_from_text(text, groq_client, model):
    """
    Extract only basic medicine information from the OCR text
    
    Args:
        text (str): The extracted text from the medicine package
        groq_client: Groq client instance
        model (str): Model name to use
        
    Returns:
        dict: Basic structured medicine information from OCR
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
        
        # Extract JSON from response if needed
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

def get_medicine_details_from_llm(basic_info, groq_client, model):
    """
    Use the LLM's knowledge to provide detailed information about the medicine
    
    Args:
        basic_info (dict): Basic information extracted from OCR
        groq_client: Groq client instance
        model (str): Model name to use
        
    Returns:
        dict: Detailed medicine information from LLM knowledge
    """
    logger.info("Getting comprehensive medicine details from LLM knowledge...")
    
    # Extract medicine identifiers from basic info
    try:
        medicine_name = basic_info.get('Medicine Name', {})
        brand_name = medicine_name.get('Brand Name', 'Unknown')
        generic_name = medicine_name.get('Generic Name', 'Unknown')
        
        # Extract composition for better medicine identification
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
    
    # Create prompt for LLM to provide detailed information
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
    
    6. Dosage Information - Please be very specific with:
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
        
        # Extract JSON from response if needed
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
    
    Args:
        basic_info (dict): Basic information extracted from OCR
        llm_details (dict): Detailed information provided by LLM
        
    Returns:
        dict: Combined medicine information
    """
    logger.info("Combining OCR-extracted info with LLM-provided details...")
    
    combined_info = {
        # OCR-extracted information
        "Medicine Name": basic_info.get("Medicine Name", {}),
        "Composition": basic_info.get("Composition", "Not found"),
        "Manufacturer Information": basic_info.get("Manufacturer Information", "Not found"),
        "Manufacturing Date": basic_info.get("Manufacturing Date", "Not found"),
        "Expiry Date": basic_info.get("Expiry Date", "Not found"),
        
        # LLM-provided information
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

def format_medicine_info(medicine_info):
    """Format medicine information for display"""
    try:
        medicine_name = medicine_info.get('Medicine Name', {})
        brand_name = medicine_name.get('Brand Name', 'Not found')
        generic_name = medicine_name.get('Generic Name', 'Not found')
    except (AttributeError, TypeError):
        brand_name = "Not found"
        generic_name = "Not found"
        
    formatted = f"""
=================================================
           MEDICINE INFORMATION
=================================================

-------- INFORMATION FROM PACKAGE --------

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

-------- COMPREHENSIVE MEDICINE DETAILS --------

DESCRIPTION:
  {medicine_info.get('Description', 'Not provided')}

STORAGE INSTRUCTIONS:
  {medicine_info.get('Storage Instructions', 'Not provided')}

USAGE INSTRUCTIONS:
  {medicine_info.get('Usage Instructions', 'Not provided')}

WARNINGS/CAUTIONS:
  {medicine_info.get('Warnings/Cautions', 'Not provided')}

SIDE EFFECTS:
  {medicine_info.get('Side Effects', 'Not provided')}

DOSAGE INFORMATION:
  {medicine_info.get('Dosage Information', 'Not provided')}

DIETARY RECOMMENDATIONS:
  {medicine_info.get('Dietary Recommendations', 'Not provided')}

DRUG INTERACTIONS:
  {medicine_info.get('Drug Interactions', 'Not provided')}
=================================================
"""
    return formatted

def main():
    parser = argparse.ArgumentParser(description="Medicine Package OCR and Analysis")
    parser.add_argument("-i", "--image", default="D:\\Visera\\Medicine_desp\\medicine_back.webp", 
                        help="Path to the medicine package image (default: D:\\Visera\\Medicine_desp\\medicine_back.webp)")
    parser.add_argument("-t", "--text_file", required=False, default=None,
                        help="Path to already extracted text file (skips OCR)")
    parser.add_argument("-o", "--output", required=False, default="medicine_info.json",
                        help="Output file for medicine information (JSON)")
    parser.add_argument("-f", "--formatted_output", required=False, default="medicine_info.txt",
                        help="Output file for formatted medicine information (text)")
    
    args = parser.parse_args()
    
    # Setup environment
    env_loaded = setup_env()
    if not env_loaded:
        logger.error("Please update the .env file with your API key and run again.")
        return
    
    # Get API key and model from environment variables
    groq_api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('MODEL', 'llama3-70b-8192')  # Default to llama3-70b-8192 if not specified
    
    # Initialize Groq client
    groq_client = Groq(api_key=groq_api_key)
    
    # Either extract text from image or load from file
    if args.text_file:
        logger.info(f"Loading text from file: {args.text_file}")
        with open(args.text_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
    else:
        # Extract text from image
        extracted_text = extract_text_from_document(args.image)
        
        # Save extracted text to file
        text_file = save_text_to_file(extracted_text)
    
    # Step 1: Extract basic info from OCR text
    basic_info = extract_basic_info_from_text(extracted_text, groq_client, model)
    
    # Step 2: Get detailed medicine information from LLM knowledge
    llm_details = get_medicine_details_from_llm(basic_info, groq_client, model)
    
    # Step 3: Combine both sources of information
    combined_info = combine_medicine_information(basic_info, llm_details)
    
    # Save combined medicine information to JSON file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(combined_info, f, indent=2)
    logger.info(f"Medicine information saved to {args.output}")
    
    # Create and save formatted output
    formatted_info = format_medicine_info(combined_info)
    with open(args.formatted_output, 'w', encoding='utf-8') as f:
        f.write(formatted_info)
    logger.info(f"Formatted medicine information saved to {args.formatted_output}")
    
    # Print formatted information
    print(formatted_info)

if __name__ == "__main__":
    main()
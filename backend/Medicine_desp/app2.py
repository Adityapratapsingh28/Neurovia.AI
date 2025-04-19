import easyocr
import cv2
import argparse
from spellchecker import SpellChecker

def extract_text_from_document(image_path):
    """
    Extract text from a document image with spelling correction
    
    Args:
        image_path (str): Path to the document image
        
    Returns:
        str: Extracted and corrected text
    """
    # Initialize the OCR reader
    print("Initializing OCR engine...")
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Initialize spell checker
    spell = SpellChecker()
    
    # Read the image
    print(f"Reading image from: {image_path}")
    results = reader.readtext(image_path)
    
    # Extract and correct text
    print("Extracting and correcting text...")
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

IMAGE_PATH = r"D:\Visera\Medicine_desp\medicine_back.webp"  # Replace ith your document path

def main():
    # Extract text
    extracted_text = extract_text_from_document(IMAGE_PATH)
    
    # Print the extracted text
    print("\n" + "="*50)
    print("EXTRACTED TEXT:")
    print("="*50)
    print(extracted_text)
    print("="*50)
    
    # Optionally save to file
    with open('extracted_text.txt', 'w', encoding='utf-8') as f:
        f.write(extracted_text)
    print(f"Text also saved to 'extracted_text.txt'")

if __name__ == "__main__":
    main()
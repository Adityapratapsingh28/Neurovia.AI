from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import markdown2
import logging
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variables
svc = None
scalar = None
llm = None
explain_chain = None
report_chain = None

def initialize_models():
    global svc, scalar, llm, explain_chain, report_chain
    
    try:
        # Load and prepare data
        df = pd.read_csv('parkinsons.data')
        X = df.drop(['name', 'status'], axis=1)
        y = df['status']
        
        # Scale features
        scalar = StandardScaler()
        X_scaled = scalar.fit_transform(X)
        
        # Train model
        svc = SVC()
        svc.fit(X_scaled, y)
        
        # Initialize LLM components
        llm = ChatGroq(
            temperature=0,
            groq_api_key="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",
            model_name="llama-3.1-8b-instant"
        )
        
        # Define prompts
        explain_prompt = PromptTemplate(
            input_variables=["features", "prediction"],
            template="""
            **Parkinson's Assessment Explanation**
            
            Prediction: {prediction}
            
            Key Features:
            {features}
            
            Interpretation:
            - Highlighting the most significant factors
            - Clinical relevance to Parkinson's
            - Simple, non-technical language
            
            Note: Clinical evaluation required for diagnosis.
            """
        )
        
        report_prompt = PromptTemplate(
            input_variables=["features", "prediction"],
            template="""
            **Medical Assessment Report**
            Date: {datetime}
            
            Result: {prediction}
            
            Notable Features:
            {features}
            
            Recommendations:
            1. Neurological consultation
            2. Further diagnostic testing
            3. Regular monitoring
            
            Disclaimer: Screening tool only (~85% accuracy).
            """
        )
        
        explain_chain = LLMChain(llm=llm, prompt=explain_prompt)
        report_chain = LLMChain(llm=llm, prompt=report_prompt)
        
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/feature_options')
def get_feature_options():
    try:
        df = pd.read_csv('parkinsons.data')
        features = df.drop(['name', 'status'], axis=1)
        
        # Get unique values for each feature (sorted)
        options = {
            col: sorted(features[col].unique().tolist())
            for col in features.columns
        }
        
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if len(data['features']) != 22:
            return jsonify({'error': 'Exactly 22 features required'}), 400
        
        # Prepare features
        features = np.array(data['features'], dtype=float)
        scaled_features = scalar.transform(features.reshape(1, -1))
        
        # Make prediction
        prediction = svc.predict(scaled_features)
        result = "Parkinson's likely present" if prediction[0] == 1 else "No Parkinson's detected"
        
        # Generate reports
        features_dict = {
            f"Feature_{i+1}": val 
            for i, val in enumerate(data['features'])
        }
        
        explanation, report = run_diagnosis_assistant(
            features_dict, 
            result
        )
        
        return jsonify({
            'prediction': result,
            'explanation': markdown2.markdown(explanation),
            'report': markdown2.markdown(report),
            'features': features_dict
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_diagnosis_assistant(features_dict, prediction):
    try:
        features_str = "\n".join(
            f"- {name}: {value:.6f}" 
            for name, value in features_dict.items()
        )
        
        explanation = explain_chain.run({
            'features': features_str,
            'prediction': prediction
        })
        
        report = report_chain.run({
            'features': features_str,
            'prediction': prediction,
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        return explanation, report
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return "Could not generate explanation", "Could not generate report"

if __name__ == '__main__':
    if initialize_models():
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        logger.error("Failed to initialize models - check logs")
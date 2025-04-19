import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
svc = None
scalar = None
llm = None
explain_chain = None
report_chain = None

def initialize_models():
    global svc, scalar, llm, explain_chain, report_chain
    
    try:
        # Load dataset
        file_path = 'parkinsons.data'
        parkinsons = pd.read_csv(file_path)
        
        # Prepare features and target
        X = parkinsons.drop(['status', 'name'], axis=1)
        Y = parkinsons['status']
        
        # Train-test split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=2)
        
        # Scale features
        scalar = StandardScaler()
        scalar.fit(X_train)
        X_train = scalar.transform(X_train)
        X_test = scalar.transform(X_test)
        
        # Train SVM model
        svc = SVC()
        svc.fit(X_train, y_train)
        
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
            - This analysis looks at 22 voice and speech characteristics
            - The most significant factors for this prediction were:
              • Feature X: [value] (measures [aspect])
              • Feature Y: [value] (measures [aspect])
              • Feature Z: [value] (measures [aspect])
            
            Note: This is a screening tool, not a diagnosis.
            """
        )
        
        report_prompt = PromptTemplate(
            input_variables=["features", "prediction"],
            template="""
            **Medical Assessment Report**
            Date: {datetime}
            
            Result: {prediction}
            
            Notable Findings:
            {features}
            
            Next Steps:
            1. Consult a neurologist
            2. Monitor symptoms
            3. Consider follow-up testing
            
            Disclaimer: This is an automated analysis.
            """
        )
        
        explain_chain = LLMChain(llm=llm, prompt=explain_prompt)
        report_chain = LLMChain(llm=llm, prompt=report_prompt)
        
        logger.info("Models initialized successfully")
        return True
        
    except FileNotFoundError:
        logger.error("Data file not found")
        return False
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        return False

def ask_chat(question):
    try:
        response = llm.invoke(f"You are a Parkinson's assistant. {question}")
        return response.content
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return "I couldn't process that request. Please try again later."

def run_diagnosis_assistant(features_dict, prediction):
    try:
        # Format features as string
        features_str = "\n".join([f"{k}: {v:.6f}" for k, v in features_dict.items()])
        
        # Get current datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Generate reports
        explanation = explain_chain.run({
            "features": features_str,
            "prediction": prediction
        })
        
        report = report_chain.run({
            "features": features_str,
            "prediction": prediction,
            "datetime": now
        })
        
        return explanation, report
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        error_msg = "Could not generate report. Please try again."
        return error_msg, error_msg

# Initialize when module loads
if __name__ == "__main__":
    initialize_models()
else:
    initialize_models()
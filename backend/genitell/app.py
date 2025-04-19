from flask import Flask, render_template, request, jsonify
import os
from dna_analysis import DNAAnalysisAgent  # Make sure this file exists and has the class

app = Flask(__name__)

# Set your API key directly here (⚠️ keep this private!)
api_key = "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"

# Initialize the DNA analysis agent
dna_agent = DNAAnalysisAgent(api_key=api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_dna():
    try:
        # Get file path from the form
        file_path = request.form['file_path']
        analyze_all = request.form.get('analyze_all', 'n').lower()
        
        # Validate file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found at the specified path'}), 400
        
        # Analyze the DNA file
        max_snps = None if analyze_all == 'y' else 10000
        analysis_report = dna_agent.analyze_dna_file(file_path, max_snps)
        
        if 'error' in analysis_report:
            return jsonify({'error': analysis_report['error']}), 400
            
        # Return the reports
        return jsonify({
            'technical_report': analysis_report['technical_report'],
            'consumer_report': analysis_report['consumer_report'],
            'validation_report': analysis_report['validation_report'],
            'summary': {
                'total_snps': analysis_report['data_summary']['total_snps_analyzed'],
                'significant_markers': len(analysis_report['data_summary']['significant_markers']),
                'file_hash': analysis_report['data_summary'].get('file_hash', 'Not available')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8082)

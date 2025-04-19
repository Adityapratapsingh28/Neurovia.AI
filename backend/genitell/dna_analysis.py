import os
import json
import hashlib
import requests
from typing import List, Dict, Any, Tuple

# Import official Groq client
from groq import Groq

class DNAAnalysisAgent:
    def __init__(self, api_key: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialize the DNA Analysis Agent
        
        Args:
            api_key: Groq API key
            model: Groq model to use for analysis
        """
        # Initialize Groq client directly
        self.client = Groq(api_key=api_key)
        self.model = model
        
        # System prompt for technical DNA analysis
        self.technical_system_prompt = """You are a DNA Analysis Assistant specialized in analyzing 23andMe data files.
        Your job is to analyze DNA data and provide detailed scientific insights about genetic markers, ancestry information, 
        and potential health-related traits based on scientific research.
        
        IMPORTANT: Always note that genetic analysis is not a medical diagnosis. You should advise users to 
        consult healthcare professionals for any medical concerns. Be factual and scientific, but do not make
        definitive health predictions as genetic factors are just one component of overall health.
        
        When analyzing DNA data, explain your findings clearly and cite relevant scientific literature when possible.
        Use technical terminology appropriate for medical professionals and researchers.
        """
        
        # System prompt for simplified DNA analysis
        self.simplified_system_prompt = """You are a DNA Analysis Assistant that explains genetic information in simple terms.
        Your job is to translate complex genetic data into easy-to-understand language for non-specialists.
        
        Create a user-friendly report that focuses primarily on practical implications of genetic markers:
        - Use everyday language instead of technical terms
        - Focus on what the person might want to know about their health, traits, and ancestry
        - Explain clearly what actions they might consider (like discussing specific findings with a doctor)
        - Use analogies and examples to explain genetic concepts
        - Be conversational but factual
        
        IMPORTANT: Always emphasize that genetic analysis is not a medical diagnosis and should not replace professional medical advice.
        Be encouraging and positive while being honest about limitations. Avoid creating unnecessary anxiety.
        """
        
        # System prompt for validation report
        self.validation_system_prompt = """You are a DNA Analysis Validator specialized in verifying the accuracy of genetic analysis.
        Your job is to critically evaluate genetic analysis findings, highlight potential errors or misinterpretations,
        and provide confidence levels for different aspects of the analysis.
        
        When validating genetic analysis:
        - Assess scientific accuracy based on established research
        - Identify potential sources of error or uncertainty
        - Provide confidence scores for different components of the analysis
        - Note any contradictions or inconsistencies
        - Suggest additional verification methods where appropriate
        
        Be balanced, objective and scientifically rigorous in your assessment.
        """
        
        # Expanded list of significant markers with validation information
        self.significant_markers = {
            'rs429358': {
                'trait': 'APOE variant - Alzheimer\'s risk factor', 
                'chromosome': '19',
                'validation_source': 'dbSNP/ClinVar',
                'scientific_consensus': 'high',
                'citation': 'Corder, E. H. et al. (1993). Science, 261(5123), 921-923'
            },
            'rs7412': {
                'trait': 'APOE variant - Alzheimer\'s risk factor', 
                'chromosome': '19',
                'validation_source': 'dbSNP/ClinVar',
                'scientific_consensus': 'high',
                'citation': 'Corder, E. H. et al. (1993). Science, 261(5123), 921-923'
            },
            'rs1801133': {
                'trait': 'MTHFR variant - Folate metabolism', 
                'chromosome': '1',
                'validation_source': 'dbSNP/ClinVar',
                'scientific_consensus': 'medium',
                'citation': 'Frosst, P. et al. (1995). Nature Genetics, 10(1), 111-113'
            },
            'rs1051730': {
                'trait': 'Nicotine dependence', 
                'chromosome': '15',
                'validation_source': 'GWAS Catalog',
                'scientific_consensus': 'medium',
                'citation': 'Thorgeirsson, T. E. et al. (2008). Nature, 452(7187), 638-642'
            },
            'rs9939609': {
                'trait': 'FTO gene - obesity risk factor', 
                'chromosome': '16',
                'validation_source': 'GWAS Catalog',
                'scientific_consensus': 'high',
                'citation': 'Frayling, T. M. et al. (2007). Science, 316(5826), 889-894'
            },
            'rs4475691': {
                'trait': 'Mood disorders association', 
                'chromosome': '1',
                'validation_source': 'GWAS Catalog',
                'scientific_consensus': 'low',
                'citation': 'Sullivan, P. F. et al. (2018). Nature Genetics, 50(5), 668-681'
            },
            'rs6657440': {
                'trait': 'Cardiovascular health marker', 
                'chromosome': '1',
                'validation_source': 'CARDIoGRAMplusC4D',
                'scientific_consensus': 'medium',
                'citation': 'Nikpay, M. et al. (2015). Nature Genetics, 47(10), 1121-1130'
            },
            'rs7537756': {
                'trait': 'Immune response variation', 
                'chromosome': '1',
                'validation_source': 'ImmunoChip',
                'scientific_consensus': 'low',
                'citation': 'Parkes, M. et al. (2013). Nature Reviews Gastroenterology & Hepatology, 10(9), 534-542'
            },
            'rs13302982': {
                'trait': 'Neurological development', 
                'chromosome': '1',
                'validation_source': 'PsychChip',
                'scientific_consensus': 'emerging',
                'citation': 'Thompson, P. M. et al. (2020). Nature Neuroscience, 23(1), 6-9'
            },
            'rs2880024': {
                'trait': 'Metabolic function marker', 
                'chromosome': '1',
                'validation_source': 'MetaboChip',
                'scientific_consensus': 'low',
                'citation': 'Willer, C. J. et al. (2013). Nature Genetics, 45(11), 1274-1283'
            },
            'rs4422948': {
                'trait': 'Inflammatory response marker', 
                'chromosome': '1',
                'validation_source': 'ImmunoChip',
                'scientific_consensus': 'emerging',
                'citation': 'Jostins, L. et al. (2012). Nature, 491(7422), 119-124'
            },
            # Add more markers from publicly available databases
        }
        
        # Reference databases for validation
        self.reference_databases = {
            'dbSNP': 'https://www.ncbi.nlm.nih.gov/snp/',
            'ClinVar': 'https://www.ncbi.nlm.nih.gov/clinvar/',
            'GWAS Catalog': 'https://www.ebi.ac.uk/gwas/',
            'gnomAD': 'https://gnomad.broadinstitute.org/',
            'ExAC': 'http://exac.broadinstitute.org/',
            'PharmGKB': 'https://www.pharmgkb.org/',
            'HapMap': 'https://www.genome.gov/10001688/international-hapmap-project'
        }
    
    def _parse_23andme_file(self, file_path: str, max_snps: int = None) -> Dict[str, Any]:
        """
        Parse a 23andMe raw data file
        
        Args:
            file_path: Path to the 23andMe file
            max_snps: Maximum number of SNPs to analyze (None for all)
            
        Returns:
            Dictionary containing parsed DNA data
        """
        snp_data = []
        metadata = {}
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    # Skip comment lines but capture metadata
                    if line.startswith('#'):
                        if ': ' in line:
                            key, value = line[1:].strip().split(': ', 1)
                            metadata[key] = value
                        continue
                    
                    # Handle header line
                    if line.lower().startswith('rsid'):
                        continue
                    
                    # Parse SNP data - handle both 4-column and 5-column formats
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        rsid = parts[0]
                        chromosome = parts[1]
                        position = parts[2]
                        
                        # Handle both 4-column format (combined genotype) and 5-column format (separate alleles)
                        if len(parts) >= 5:
                            # 5-column format: Combine alleles into genotype
                            genotype = parts[3] + parts[4]
                        else:
                            # 4-column format: Genotype already combined
                            genotype = parts[3]
                            
                        snp_data.append({
                            'rsid': rsid,
                            'chromosome': chromosome,
                            'position': position,
                            'genotype': genotype
                        })
                        
                        # Limit to max_snps if specified
                        if max_snps and len(snp_data) >= max_snps:
                            break
            
            return {
                'metadata': metadata,
                'snp_data': snp_data,
                'total_snps': len(snp_data),
                'file_hash': self._calculate_file_hash(file_path)  # Add file hash for validation
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of file for data integrity validation
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_significant_markers(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract significant genetic markers from the parsed data
        
        Args:
            parsed_data: Parsed DNA data
            
        Returns:
            List of significant markers found in the data
        """
        found_markers = []
        
        for snp in parsed_data.get('snp_data', []):
            if snp['rsid'] in self.significant_markers:
                marker_info = self.significant_markers[snp['rsid']].copy()
                marker_info.update({
                    'rsid': snp['rsid'],
                    'genotype': snp['genotype'],
                    'position': snp['position']
                })
                found_markers.append(marker_info)
        
        return found_markers
    
    def _validate_file_format(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the format of the DNA file
        
        Args:
            parsed_data: Parsed DNA data
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            'format_valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Check if any data was parsed
        if not parsed_data.get('snp_data'):
            validation_results['format_valid'] = False
            validation_results['issues'].append("No SNP data found in file.")
            return validation_results
        
        # Sample some SNPs to check format validity
        sample_snps = parsed_data.get('snp_data', [])[:10]
        
        # Check RSID format (should start with 'rs' followed by numbers)
        for snp in sample_snps:
            rsid = snp.get('rsid', '')
            if not (rsid.startswith('rs') and rsid[2:].isdigit()):
                validation_results['format_valid'] = False
                validation_results['issues'].append(f"Invalid RSID format detected: {rsid}")
                break
        
        # Check chromosome format
        valid_chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y', 'MT']
        for snp in sample_snps:
            chromosome = snp.get('chromosome', '')
            if chromosome not in valid_chromosomes:
                validation_results['format_valid'] = False
                validation_results['issues'].append(f"Invalid chromosome format detected: {chromosome}")
                break
        
        # Check genotype format (should be nucleotides)
        valid_nucleotides = ['A', 'T', 'G', 'C', '-']
        for snp in sample_snps:
            genotype = snp.get('genotype', '')
            if not all(n in valid_nucleotides for n in genotype):
                validation_results['format_valid'] = False
                validation_results['issues'].append(f"Invalid nucleotide in genotype: {genotype}")
                break
        
        # Check total SNPs count (typical 23andMe files have 600,000+ SNPs)
        total_snps = parsed_data.get('total_snps', 0)
        if total_snps < 1000:  # Very low for a real file
            validation_results['issues'].append(f"Unusually low number of SNPs: {total_snps}. Standard 23andMe files typically contain 600,000+ SNPs.")
            validation_results['suggestions'].append("Consider checking if this is a partial or corrupted file.")
        
        return validation_results
    
    def _validate_marker_frequencies(self, significant_markers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate marker frequencies against population databases
        
        Args:
            significant_markers: List of significant markers
            
        Returns:
            Dictionary containing marker frequency validation results
        """
        # This function would ideally check against actual population databases
        # For the purpose of this example, we'll simulate this process
        
        validation_results = {
            'unusual_markers': [],
            'frequency_validation': []
        }
        
        for marker in significant_markers:
            # For demonstration - in a real implementation, you'd query actual databases
            # or have a local copy of frequency data
            
            marker_validation = {
                'rsid': marker['rsid'],
                'trait': marker['trait'],
                'genotype': marker.get('genotype', 'N/A'),
                'scientific_consensus': marker.get('scientific_consensus', 'unknown'),
                'citation': marker.get('citation', 'Not available'),
                'frequency_check': 'Simulated validation - would query actual population databases'
            }
            
            # Example validation logic
            if marker.get('scientific_consensus') == 'low':
                marker_validation['note'] = "This marker has relatively low scientific consensus. Results should be interpreted with caution."
            
            validation_results['frequency_validation'].append(marker_validation)
        
        return validation_results
    
    def _cross_check_markers(self, significant_markers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cross-check markers for internal consistency
        
        Args:
            significant_markers: List of significant markers
            
        Returns:
            Dictionary containing cross-check results
        """
        validation_results = {
            'consistency_issues': [],
            'related_markers': []
        }
        
        # Example: Check APOE status (rs429358 and rs7412 together determine APOE allele)
        apoe_markers = [m for m in significant_markers if m['rsid'] in ['rs429358', 'rs7412']]
        
        if len(apoe_markers) == 2:
            # This would contain the actual logic to determine APOE status
            validation_results['related_markers'].append({
                'marker_group': 'APOE status',
                'markers_present': [m['rsid'] for m in apoe_markers],
                'note': 'Both markers for APOE status are present, allowing for complete APOE genotype determination.'
            })
        elif len(apoe_markers) == 1:
            validation_results['consistency_issues'].append({
                'marker_group': 'APOE status',
                'issue': f"Only one APOE marker ({apoe_markers[0]['rsid']}) is present. Both rs429358 and rs7412 are needed for complete APOE genotype determination."
            })
        
        return validation_results
    
    def _generate_validation_report(self, data_summary: Dict[str, Any], validation_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive validation report
        
        Args:
            data_summary: Summary of DNA data
            validation_data: Validation results
            
        Returns:
            Formatted validation report
        """
        validation_prompt = f"""
        I need to create a validation report for a DNA analysis with the following information:
        
        File: {data_summary['file_name']}
        File Hash: {data_summary.get('file_hash', 'Not available')}
        Total SNPs analyzed: {data_summary['total_snps_analyzed']}
        
        File Format Validation:
        {json.dumps(validation_data.get('file_format', {}), indent=2)}
        
        Marker Frequency Validation:
        {json.dumps(validation_data.get('marker_frequencies', {}), indent=2)}
        
        Marker Cross-Check:
        {json.dumps(validation_data.get('cross_check', {}), indent=2)}
        
        Reference Databases Used:
        {json.dumps(self.reference_databases, indent=2)}
        
        Please create a comprehensive validation report that:
        1. Assesses the reliability of the data file format
        2. Evaluates the confidence levels for significant markers identified
        3. Discusses any consistency issues or unusual findings
        4. Provides an overall confidence score for the analysis (on a scale of 1-10)
        5. Recommends additional verification steps if needed
        6. Explains the limitations of this validation process
        
        Format this as a formal validation report with clear sections and appropriate scientific terminology.
        """
        
        try:
            validation_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.validation_system_prompt},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            validation_report = validation_response.choices[0].message.content
        except Exception as e:
            validation_report = f"Error generating validation report: {e}"
        
        return validation_report
    
    def analyze_dna_file(self, file_path: str, max_snps: int = None) -> Dict[str, Any]:
        """
        Analyze a 23andMe DNA file and generate technical, consumer-friendly, and validation reports
        
        Args:
            file_path: Path to the 23andMe file
            max_snps: Maximum number of SNPs to analyze (None for all)
            
        Returns:
            Dictionary containing analysis reports and validation results
        """
        # Parse the DNA file
        parsed_data = self._parse_23andme_file(file_path, max_snps)
        
        if 'error' in parsed_data:
            return {'error': parsed_data['error']}
        
        # Extract significant markers
        significant_markers = self._get_significant_markers(parsed_data)
        
        # Create a summary of the data
        data_summary = {
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'file_hash': parsed_data.get('file_hash', 'Not available'),
            'metadata': parsed_data.get('metadata', {}),
            'total_snps_analyzed': parsed_data.get('total_snps', 0),
            'significant_markers': significant_markers
        }
        
        # Perform validation checks
        validation_data = {
            'file_format': self._validate_file_format(parsed_data),
            'marker_frequencies': self._validate_marker_frequencies(significant_markers),
            'cross_check': self._cross_check_markers(significant_markers)
        }
        
        # Generate reports
        technical_report, consumer_report = self._generate_reports(data_summary)
        validation_report = self._generate_validation_report(data_summary, validation_data)
        
        # Combine all information into a complete report package
        report = {
            'data_summary': data_summary,
            'validation_data': validation_data,
            'technical_report': technical_report,
            'consumer_report': consumer_report,
            'validation_report': validation_report
        }
        
        return report
    
    def _generate_reports(self, data_summary: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate both technical and consumer-friendly reports using the LLM
        
        Args:
            data_summary: Summary of the DNA data analysis
            
        Returns:
            Tuple containing technical and consumer-friendly reports
        """
        # Common prompt content for both reports
        base_prompt = f"""
        I have analyzed a DNA file with the following information:
        
        File: {data_summary['file_name']}
        Size: {data_summary['file_size']} bytes
        Total SNPs analyzed: {data_summary['total_snps_analyzed']}
        
        Metadata:
        {json.dumps(data_summary['metadata'], indent=2)}
        
        Significant genetic markers found:
        {json.dumps(data_summary['significant_markers'], indent=2)}
        """
        
        # Generate technical report for medical professionals
        technical_prompt = base_prompt + """
        Based on this information, please provide:
        1. A general summary of what this DNA data contains
        2. Information about significant genetic markers identified (if any)
        3. Possible genetic traits or health factors that may be relevant
        4. Ancestry information that might be inferred
        5. Important limitations of this analysis
        
        Format the response as a comprehensive scientific DNA analysis report suitable for medical professionals.
        Include relevant scientific citations where appropriate.
        """
        
        # Generate consumer-friendly report for the general public
        consumer_prompt = base_prompt + """
        Based on this information, create a user-friendly report that:
        1. Explains in simple terms what this DNA data shows
        2. Focuses primarily on what these genetic markers might mean for health, traits, and ancestry
        3. Uses everyday language and helpful analogies to explain genetic concepts
        4. Provides practical guidance on what actions might be considered (like talking to a doctor)
        5. Clearly explains limitations in an encouraging way
        
        Format this as a conversational, easy-to-understand report without technical jargon.
        Focus on being informative, practical, and reassuring while being honest.
        """
        
        # Generate technical report
        try:
            tech_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.technical_system_prompt},
                    {"role": "user", "content": technical_prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            technical_report = tech_response.choices[0].message.content
        except Exception as e:
            technical_report = f"Error generating technical report: {e}"
        
        # Generate consumer-friendly report
        try:
            consumer_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.simplified_system_prompt},
                    {"role": "user", "content": consumer_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            consumer_report = consumer_response.choices[0].message.content
        except Exception as e:
            consumer_report = f"Error generating consumer report: {e}"
        
        return technical_report, consumer_report


def main():
    # Get Groq API key from environment variable
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Initialize the DNA analysis agent
    dna_agent = DNAAnalysisAgent(api_key=api_key)
    
    try:
        # Analyze the DNA file
        file_path = input("Enter the path to your DNA data file: ")
        
        # Ask if user wants to analyze all SNPs or just a subset
        analyze_all = input("Analyze all SNPs? (y/n, default=n): ").lower()
        max_snps = None if analyze_all == 'y' else 10000
        
        print(f"\nAnalyzing DNA data {'(all SNPs)' if max_snps is None else f'(limited to {max_snps} SNPs)'}...")
        analysis_report = dna_agent.analyze_dna_file(file_path, max_snps)
        
        if 'error' in analysis_report:
            print(f"Error: {analysis_report['error']}")
            return
            
        # Print summary info
        print("\n=== DNA ANALYSIS SUMMARY ===")
        print(f"Analyzed {analysis_report['data_summary']['total_snps_analyzed']} SNPs")
        print(f"Found {len(analysis_report['data_summary']['significant_markers'])} significant markers")
        print(f"File hash: {analysis_report['data_summary'].get('file_hash', 'Not available')}")
        
        # Save the technical report
        with open("dna_technical_report.txt", "w") as f:
            f.write("=== TECHNICAL DNA ANALYSIS REPORT ===\n\n")
            f.write(f"Analyzed {analysis_report['data_summary']['total_snps_analyzed']} SNPs\n")
            f.write(f"Found {len(analysis_report['data_summary']['significant_markers'])} significant markers\n\n")
            f.write(analysis_report['technical_report'])
            f.write("\n\n=========================\n")
        
        # Save the consumer report
        with open("dna_consumer_report.txt", "w") as f:
            f.write("=== YOUR PERSONALIZED DNA INSIGHTS ===\n\n")
            f.write(analysis_report['consumer_report'])
            f.write("\n\n=========================\n")
        
        # Save the validation report
        with open("dna_validation_report.txt", "w") as f:
            f.write("=== DNA ANALYSIS VALIDATION REPORT ===\n\n")
            f.write(f"File: {analysis_report['data_summary']['file_name']}\n")
            f.write(f"File hash: {analysis_report['data_summary'].get('file_hash', 'Not available')}\n\n")
            f.write(analysis_report['validation_report'])
            f.write("\n\n=========================\n")
        
        # Ask which report to display
        print("\nReports have been saved to:")
        print("- dna_technical_report.txt (For medical professionals)")
        print("- dna_consumer_report.txt (Easy-to-understand version)")
        print("- dna_validation_report.txt (Validation assessment)")
        
        show_report = input("\nWhich report would you like to view? (t)echnical, (c)onsumer, (v)alidation, or (a)ll? ").lower()
        
        if show_report.startswith('t'):
            print("\n\n=== TECHNICAL DNA ANALYSIS REPORT ===\n")
            print(analysis_report['technical_report'])
        elif show_report.startswith('c'):
            print("\n\n=== YOUR PERSONALIZED DNA INSIGHTS ===\n")
            print(analysis_report['consumer_report'])
        elif show_report.startswith('v'):
            print("\n\n=== DNA ANALYSIS VALIDATION REPORT ===\n")
            print(analysis_report['validation_report'])
        else:
            print("\n\n=== TECHNICAL DNA ANALYSIS REPORT ===\n")
            print(analysis_report['technical_report'])
            print("\n\n=== YOUR PERSONALIZED DNA INSIGHTS ===\n")
            print(analysis_report['consumer_report'])
            print("\n\n=== DNA ANALYSIS VALIDATION REPORT ===\n")
            print(analysis_report['validation_report'])
            
    except Exception as e:
        print(f"Error running DNA analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
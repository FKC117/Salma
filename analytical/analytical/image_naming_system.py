
# Add this to sandbox_executor.py or sandbox_result_processor.py

def generate_descriptive_image_name(image_index, analysis_context=None):
    """Generate a descriptive name for generated images"""
    
    # Analysis type mapping based on common patterns
    analysis_types = [
        "Temporal Trends Analysis",
        "Geographical Comparison Chart", 
        "Correlation Analysis Heatmap",
        "Prevalence Distribution Chart",
        "Mental Health Trends Overview",
        "Statistical Summary Plot",
        "Data Visualization Chart",
        "Analytical Insights Graph",
        "Pattern Recognition Chart",
        "Comparative Analysis Plot"
    ]
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Select analysis type based on index or context
    if analysis_context:
        # Use context to determine type
        analysis_type = analysis_context.get('type', analysis_types[image_index % len(analysis_types)])
    else:
        analysis_type = analysis_types[image_index % len(analysis_types)]
    
    # Create unique name
    return f"{analysis_type} ({timestamp})"

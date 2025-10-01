"""
Script to activate the correlation analysis tool
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import AnalysisTool

def activate_correlation_tool():
    """Activate the correlation analysis tool"""
    try:
        # Try to get the correlation analysis tool
        tool = AnalysisTool.objects.get(name='correlation_analysis')
        print(f"Found correlation analysis tool: {tool.display_name}")
        
        # Activate the tool
        tool.is_active = True
        tool.save()
        print("Correlation analysis tool activated successfully!")
        
        return True
    except AnalysisTool.DoesNotExist:
        print("Correlation analysis tool not found in database")
        print("You may need to run the tool registration command first")
        return False
    except Exception as e:
        print(f"Error activating correlation analysis tool: {str(e)}")
        return False

if __name__ == "__main__":
    activate_correlation_tool()
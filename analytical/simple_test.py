import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.conf import settings

print("USE_OLLAMA:", settings.USE_OLLAMA)
print("GOOGLE_AI_API_KEY exists:", bool(settings.GOOGLE_AI_API_KEY))
import sys
import os
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.attendance_service import auto_mark_absences_service

if __name__ == "__main__":
    try:
        print("Running auto-absence service...")
        count = auto_mark_absences_service()
        print(f"Successfully marked {count} absences.")
    except Exception as e:
        print(f"Error: {e}")
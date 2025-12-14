import os
import sys
from dotenv import load_dotenv

def smoke_test():
    print("Running Smoke Test...")
    
    # 1. Check Python Version
    print(f"Python Version: {sys.version}")
    
    # 2. Check Environment Variables
    load_dotenv()
    api_key = os.getenv("RAGFLOW_API_KEY")
    print(f"RAGFLOW_API_KEY present: {'Yes' if api_key else 'No'}")
    
    # 3. Check Imports
    try:
        try:
            import autogen
            print("Import autogen: SUCCESS (autogen)")
        except ImportError:
            import pyautogen as autogen
            print("Import autogen: SUCCESS (pyautogen)")
    except ImportError as e:
        print(f"Import autogen: FAILED ({e})")
        return False
        
    try:
        import pydantic
        print("Import pydantic: SUCCESS")
    except ImportError as e:
        print(f"Import pydantic: FAILED ({e})")
        return False

    try:
        import requests
        print("Import requests: SUCCESS")
    except ImportError as e:
        print(f"Import requests: FAILED ({e})")
        return False

    print("Smoke Test: ERROR FREE (Logic pending RAGFlow connection)")
    return True

if __name__ == "__main__":
    success = smoke_test()
    if not success:
        sys.exit(1)

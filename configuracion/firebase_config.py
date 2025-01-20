import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from dotenv import load_dotenv

load_dotenv()

def inicializar_firebase():
    """Initialize Firebase with proper serverless support"""
    if not firebase_admin._apps:
        try:
            # Check if running on Vercel
            if os.environ.get('VERCEL'):
                # Get credentials from environment variable
                cred_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS_PATH', '{}'))
                cred = credentials.Certificate(cred_dict)
            else:
                # Local development - use file path
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
                cred = credentials.Certificate(cred_path)
            
            # Initialize with specific options for serverless
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
            })
            
            db = firestore.client()
            print("Firebase connection established successfully")
            return db
        except Exception as e:
            print(f"Error connecting to Firebase: {str(e)}")
            raise e
    return firestore.client()
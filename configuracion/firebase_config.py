#BACKEND configuracion\firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os


load_dotenv()

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Usar directamente el JSON de credenciales en lugar del archivo
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": "hackaton-b96e0",
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
            })
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            print(f"Error al conectar con Firebase: {str(e)}")
            raise e
    return firestore.client()
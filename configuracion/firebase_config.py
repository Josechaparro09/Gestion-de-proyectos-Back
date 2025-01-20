#BACKEND configuracion\firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os


load_dotenv()

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            cred_path = 'hackaton-b96e0-firebase-adminsdk-mcv6w-d484e4c384.json'
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Conexión con Firebase establecida correctamente")
            return db
        except Exception as e:
            print(f"Error al conectar con Firebase: {str(e)}")
            raise e
    return firestore.client()
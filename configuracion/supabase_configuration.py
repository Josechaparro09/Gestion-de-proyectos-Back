from supabase import create_client, Client
import os
from typing import Optional
from dotenv import load_dotenv

def inicializar_supabase() -> Optional[Client]:
    try:
        # Cargar variables de entorno desde .env si existe
        load_dotenv()
        
        # Obtener credenciales
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        # Validar que existan las credenciales
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL y SUPABASE_KEY deben estar configuradas en las variables de entorno"
            )
        
        # Crear y retornar el cliente
        supabase: Client = create_client(url, key)
        return supabase
        
    except Exception as e:
        print(f"Error al inicializar Supabase: {str(e)}")
        return None

# Ejemplo de uso
def obtener_supabase() -> Client:

    if not hasattr(obtener_supabase, "_instance"):
        client = inicializar_supabase()
        if client is None:
            raise RuntimeError("No se pudo inicializar Supabase")
        obtener_supabase._instance = client
    return obtener_supabase._instance
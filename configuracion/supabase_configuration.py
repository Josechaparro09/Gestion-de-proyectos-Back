# configuracion/supabase_configuration.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def inicializar_supabase() -> Client:
    """
    Inicializa y retorna un cliente de Supabase
    
    Returns:
        Client: Cliente de Supabase configurado
    """
    url: str = os.getenv('SUPABASE_URL')
    key: str = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("Las credenciales de Supabase no están configuradas correctamente")
    
    supabase: Client = create_client(url, key)
    return supabase

# Variable global para acceder al cliente de Supabase
supabase_client = inicializar_supabase()
# utils/storage_utils.py
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
from typing import Dict, Any, Optional

from configuracion.supabase_configuration import supabase_client

BUCKET_NAME = "archivos"
BASE_PATH = "proyectos"

def generar_nombre_unico(filename: str) -> str:
    """
    Genera un nombre de archivo único basado en la fecha y un UUID
    
    Args:
        filename (str): Nombre original del archivo
    
    Returns:
        str: Nombre de archivo único
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = os.path.splitext(filename)[1]
    nombre_unico = f"{timestamp}_{uuid.uuid4()}{extension}"
    return secure_filename(nombre_unico)

def subir_archivo_supabase(
    archivo, 
    proyecto_id: str, 
    subcarpeta: str = '', 
    usuario_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sube un archivo a Supabase Storage
    
    Args:
        archivo: Objeto de archivo a subir
        proyecto_id (str): ID del proyecto
        subcarpeta (str, optional): Subcarpeta dentro del proyecto
        usuario_id (str, optional): ID del usuario que sube el archivo
    
    Returns:
        Dict[str, Any]: Metadatos del archivo subido
    """
    try:
        # Generar nombre único para el archivo
        nombre_archivo = generar_nombre_unico(archivo.filename)
        
        # Construir ruta de almacenamiento
        ruta_storage = f"{BASE_PATH}/{proyecto_id}"
        if subcarpeta:
            ruta_storage += f"/{subcarpeta}"
        ruta_completa = f"{ruta_storage}/{nombre_archivo}"
        
        # Leer contenido del archivo
        contenido = archivo.read()
        
        # Subir archivo a Supabase Storage
        respuesta = supabase_client.storage.from_(BUCKET_NAME).upload(
            path=ruta_completa, 
            file=contenido,
            file_options={
                "content-type": archivo.content_type
            }
        )
        
        # Obtener URL pública del archivo
        url_publica = supabase_client.storage.from_(BUCKET_NAME).get_public_url(ruta_completa)
        
        # Preparar metadatos del archivo
        metadata = {
            "nombre_original": archivo.filename,
            "nombre_storage": nombre_archivo,
            "ruta_storage": ruta_completa,
            "url": url_publica,
            "tipo_mime": archivo.content_type,
            "tamano": len(contenido),
            "fecha_subida": datetime.now().isoformat(),
            "subido_por": usuario_id
        }
        
        return metadata
    
    except Exception as e:
        print(f"Error al subir archivo a Supabase: {str(e)}")
        raise

def eliminar_archivo_supabase(ruta_storage: str) -> bool:
    """
    Elimina un archivo de Supabase Storage
    
    Args:
        ruta_storage (str): Ruta completa del archivo en Supabase Storage
    
    Returns:
        bool: True si el archivo fue eliminado exitosamente, False en caso contrario
    """
    try:
        respuesta = supabase_client.storage.from_(BUCKET_NAME).remove([ruta_storage])
        return True
    except Exception as e:
        print(f"Error al eliminar archivo de Supabase: {str(e)}")
        return False

def listar_archivos_proyecto(proyecto_id: str) -> list:
    """
    Lista todos los archivos de un proyecto en Supabase Storage
    
    Args:
        proyecto_id (str): ID del proyecto
    
    Returns:
        list: Lista de archivos del proyecto
    """
    try:
        ruta_base = f"{BASE_PATH}/{proyecto_id}"
        respuesta = supabase_client.storage.from_(BUCKET_NAME).list(path=ruta_base)
        return respuesta
    except Exception as e:
        print(f"Error al listar archivos en Supabase: {str(e)}")
        return []
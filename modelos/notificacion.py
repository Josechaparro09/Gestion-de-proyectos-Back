from configuracion.firebase_config import NOTIFICACIONES
from datetime import datetime

def enviar_notificacion(usuario_id, titulo, mensaje, tipo='info'):
    try:
        notificacion = {
            'usuario_id': usuario_id,
            'titulo': titulo,
            'mensaje': mensaje,
            'tipo': tipo,
            'fecha': datetime.now(),
            'leida': False
        }
        
        NOTIFICACIONES.add(notificacion)
        return True
        
    except Exception as e:
        print(f"Error al enviar notificación: {str(e)}")
        return False

def get_notificaciones_usuario(usuario_id):
    try:
        notificaciones = NOTIFICACIONES.where('usuario_id', '==', usuario_id).get()
        return [doc.to_dict() for doc in notificaciones]
    except Exception as e:
        print(f"Error al obtener notificaciones: {str(e)}")
        return []
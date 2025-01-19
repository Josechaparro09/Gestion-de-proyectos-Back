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
        
        # Guardar en Firestore
        NOTIFICACIONES.add(notificacion)
        return True
        
    except Exception as e:
        print(f"Error al enviar notificación: {str(e)}")
        return False

def marcar_como_leida(notificacion_id):
    try:
        NOTIFICACIONES.document(notificacion_id).update({
            'leida': True,
            'fecha_lectura': datetime.now()
        })
        return True
    except Exception as e:
        print(f"Error al marcar notificación como leída: {str(e)}")
        return False

def obtener_notificaciones_usuario(usuario_id, solo_no_leidas=False):
    try:
        query = NOTIFICACIONES.where('usuario_id', '==', usuario_id)
        if solo_no_leidas:
            query = query.where('leida', '==', False)
        
        notificaciones = query.order_by('fecha', direction='DESCENDING').get()
        return [doc.to_dict() for doc in notificaciones]
    except Exception as e:
        print(f"Error al obtener notificaciones: {str(e)}")
        return []
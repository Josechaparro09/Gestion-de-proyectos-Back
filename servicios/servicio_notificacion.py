#BACKEND servicios\servicio_notificacion.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

notificacion_bp = Blueprint('notificacion', __name__)
db = inicializar_firebase()
NOTIFICACIONES = db.collection('notifications')

@notificacion_bp.route('/crear', methods=['POST'])
def crear_notificacion():
    try:
        datos = request.get_json()
        
        nueva_notificacion = {
            'tipo': datos.get('tipo'),
            'mensaje': datos.get('mensaje'),
            'projectId': datos.get('projectId'),
            'destinatarios': datos.get('destinatarios', []),
            'leido': [],
            'createdAt': datetime.now().isoformat(),
            'prioridad': datos.get('prioridad', 'MEDIA'),
            'accion': {
                'tipo': datos.get('accion_tipo'),
                'url': datos.get('accion_url')
            },
            'metadata': datos.get('metadata', {})
        }
        
        doc_ref = NOTIFICACIONES.add(nueva_notificacion)
        
        return jsonify({
            'mensaje': 'Notificación creada exitosamente',
            'id': doc_ref[1].id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@notificacion_bp.route('/usuario/<user_id>', methods=['GET'])
def obtener_notificaciones_usuario(user_id):
    try:
        # Obtener notificaciones donde el usuario está en la lista de destinatarios
        notificaciones = NOTIFICACIONES.where('destinatarios', 'array_contains', user_id)\
                                     .order_by('createdAt', direction=firestore.Query.DESCENDING)\
                                     .limit(50)\
                                     .get()
        
        return jsonify([{
            'id': doc.id,
            **doc.to_dict(),
            'no_leida': user_id not in doc.to_dict().get('leido', [])
        } for doc in notificaciones])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@notificacion_bp.route('/marcar-leida/<notificacion_id>', methods=['POST'])
def marcar_como_leida(notificacion_id):
    try:
        datos = request.get_json()
        user_id = datos.get('userId')
        
        if not user_id:
            return jsonify({'error': 'Se requiere el ID del usuario'}), 400
            
        NOTIFICACIONES.document(notificacion_id).update({
            'leido': firestore.ArrayUnion([user_id])
        })
        
        return jsonify({'mensaje': 'Notificación marcada como leída'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def enviar_notificacion_cambio_fase(proyecto_id, fase, estado):
    """Utilidad para enviar notificación cuando cambia el estado de una fase"""
    try:
        # Obtener información del proyecto
        proyecto = db.collection('proyectos').document(proyecto_id).get().to_dict()
        
        destinatarios = [
            proyecto.get('lider_id'),
            proyecto.get('docente_id')
        ]
        if proyecto.get('colaboradores'):
            destinatarios.extend(proyecto.get('colaboradores'))
            
        nueva_notificacion = {
            'tipo': 'CAMBIO_ESTADO',
            'mensaje': f'La fase {fase} del proyecto {proyecto.get("titulo")} ha sido marcada como {estado}',
            'projectId': proyecto_id,
            'destinatarios': list(filter(None, destinatarios)),
            'leido': [],
            'createdAt': datetime.now().isoformat(),
            'prioridad': 'ALTA',
            'accion': {
                'tipo': 'VER_PROYECTO',
                'url': f'/proyecto/{proyecto_id}'
            }
        }
        
        NOTIFICACIONES.add(nueva_notificacion)
        return True
    except Exception as e:
        print(f"Error al enviar notificación: {str(e)}")
        return False

def enviar_notificacion_deadline(proyecto_id, entrega):
    """Utilidad para enviar notificación de fechas límite próximas"""
    try:
        proyecto = db.collection('proyectos').document(proyecto_id).get().to_dict()
        
        nueva_notificacion = {
            'tipo': 'DEADLINE',
            'mensaje': f'Próxima entrega: {entrega.get("titulo")} del proyecto {proyecto.get("titulo")}',
            'projectId': proyecto_id,
            'destinatarios': [proyecto.get('lider_id'), proyecto.get('docente_id')],
            'leido': [],
            'createdAt': datetime.now().isoformat(),
            'prioridad': 'ALTA',
            'accion': {
                'tipo': 'VER_ENTREGA',
                'url': f'/proyecto/{proyecto_id}/entrega/{entrega.get("id")}'
            }
        }
        
        NOTIFICACIONES.add(nueva_notificacion)
        return True
    except Exception as e:
        print(f"Error al enviar notificación: {str(e)}")
        return False
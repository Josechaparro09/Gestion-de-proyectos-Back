# BACKEND servicios/servicio_docente.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

docente_bp = Blueprint('docente', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

@docente_bp.route('/mis-proyectos/<docente_id>', methods=['GET'])
def obtener_proyectos(docente_id):
    try:
        print(f"Obteniendo proyectos para docente_id: {docente_id}")  # Log
        proyectos = PROYECTOS.where('docente_id', '==', docente_id).get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        print(f"Error: {e}")  # Log del error
        return jsonify({'error': str(e)}), 400


@docente_bp.route('/<proyecto_id>/comentar', methods=['POST'])
def comentar_proyecto(proyecto_id):
   try:
       datos = request.get_json()
       comentario = {
           'texto': datos.get('texto'),
           'docente_id': datos.get('docente_id'),
           'fecha': str(datetime.now())
       }
       
       PROYECTOS.document(proyecto_id).update({
           'comentarios_docente': firestore.ArrayUnion([comentario])
       })
       return jsonify({'mensaje': 'Comentario agregado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@docente_bp.route('/<proyecto_id>/tarea/<tarea_id>/comentar', methods=['POST'])
def comentar_tarea(proyecto_id, tarea_id):
   try:
       datos = request.get_json()
       nuevo_comentario = {
           'texto': datos.get('texto'),
           'docente_id': datos.get('docente_id'),
           'fecha': str(datetime.now())
       }
       
       proyecto = PROYECTOS.document(proyecto_id).get().to_dict()
       tareas = proyecto.get('tareas', [])
       
       for i, tarea in enumerate(tareas):
           if tarea.get('id') == tarea_id:
               if 'comentarios_docente' not in tarea:
                   tarea['comentarios_docente'] = []
               tarea['comentarios_docente'].append(nuevo_comentario)
               
       PROYECTOS.document(proyecto_id).update({'tareas': tareas})
       return jsonify({'mensaje': 'Comentario agregado a la tarea'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@docente_bp.route('/docente/<id>', methods=['GET'])
def obtener_docente(id):
    try:
        docente_ref = db.collection('usuarios').document(id)
        docente = docente_ref.get()

        if docente.exists:
            return jsonify(docente.to_dict())
        else:
            return jsonify({'error': 'Docente no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@docente_bp.route('/proyecto/<proyecto_id>/fase/<fase>/comentar', methods=['POST'])
def comentar_fase(proyecto_id, fase):
    try:
        # Obtener datos del request
        data = request.get_json()
        comentario = data.get('comentario')
        docente_id = data.get('docente_id')  # ID del docente que comenta

        if not comentario:
            return jsonify({
                'error': 'El comentario no puede estar vacío'
            }), 400

        # Referencia al documento del proyecto
        proyecto_ref = db.collection('proyectos').document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({
                'error': 'Proyecto no encontrado'
            }), 404

        # Crear el nuevo comentario
        nuevo_comentario = {
            'texto': comentario,
            'docente_id': docente_id,
            'fecha': datetime.now().isoformat(),
            'tipo': 'retroalimentacion'
        }

        # Actualizar el documento
        # Si la fase no existe o no tiene comentarios, se crearán automáticamente
        proyecto_ref.update({
            f'fases.{fase}.comentarios': firestore.ArrayUnion([nuevo_comentario])
        })

        return jsonify({
            'mensaje': 'Comentario agregado exitosamente',
            'comentario': nuevo_comentario
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error al agregar comentario: {str(e)}'
        }), 500
        
@docente_bp.route('/proyecto/<proyecto_id>/fase/<fase>/comentarios', methods=['GET'])
def obtener_comentarios_fase(proyecto_id, fase):
    try:
        # Referencia al documento del proyecto
        proyecto_ref = db.collection('proyectos').document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({
                'error': 'Proyecto no encontrado'
            }), 404

        # Obtener los datos del proyecto
        proyecto_data = proyecto.to_dict()
        
        # Obtener comentarios de la fase específica
        comentarios = proyecto_data.get('fases', {}).get(fase, {}).get('comentarios', [])

        return jsonify({
            'comentarios': comentarios
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error al obtener comentarios: {str(e)}'
        }), 500


@docente_bp.route('/proyecto/<proyecto_id>/fase/<fase>/comentario/<int:comentario_index>', methods=['PUT'])
def editar_comentario(proyecto_id, fase, comentario_index):
    try:
        data = request.get_json()
        nuevo_texto = data.get('comentario')
        docente_id = data.get('docente_id')

        if not nuevo_texto:
            return jsonify({
                'error': 'El comentario no puede estar vacío'
            }), 400

        # Referencia al documento del proyecto
        proyecto_ref = db.collection('proyectos').document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({
                'error': 'Proyecto no encontrado'
            }), 404

        # Obtener datos actuales
        proyecto_data = proyecto.to_dict()
        comentarios = proyecto_data.get('fases', {}).get(fase, {}).get('comentarios', [])

        if comentario_index >= len(comentarios):
            return jsonify({
                'error': 'Índice de comentario no válido'
            }), 404

        # Verificar que el docente sea el autor del comentario
        if comentarios[comentario_index].get('docente_id') != docente_id:
            return jsonify({
                'error': 'No tienes permiso para editar este comentario'
            }), 403

        # Actualizar el comentario
        comentarios[comentario_index].update({
            'texto': nuevo_texto,
            'fecha_edicion': datetime.now().isoformat()
        })

        # Actualizar el documento
        proyecto_ref.update({
            f'fases.{fase}.comentarios': comentarios
        })

        return jsonify({
            'mensaje': 'Comentario actualizado exitosamente',
            'comentario': comentarios[comentario_index]
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error al editar comentario: {str(e)}'
        }), 500



@docente_bp.route('/proyecto/<proyecto_id>/fase/<fase>/comentario/<int:comentario_index>', methods=['DELETE'])
def eliminar_comentario(proyecto_id, fase, comentario_index):
    try:
        docente_id = request.args.get('docente_id')

        # Referencia al documento del proyecto
        proyecto_ref = db.collection('proyectos').document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({
                'error': 'Proyecto no encontrado'
            }), 404

        # Obtener datos actuales
        proyecto_data = proyecto.to_dict()
        comentarios = proyecto_data.get('fases', {}).get(fase, {}).get('comentarios', [])

        if comentario_index >= len(comentarios):
            return jsonify({
                'error': 'Índice de comentario no válido'
            }), 404

        # Verificar que el docente sea el autor del comentario
        if comentarios[comentario_index].get('docente_id') != docente_id:
            return jsonify({
                'error': 'No tienes permiso para eliminar este comentario'
            }), 403

        # Eliminar el comentario
        comentarios.pop(comentario_index)

        # Actualizar el documento
        proyecto_ref.update({
            f'fases.{fase}.comentarios': comentarios
        })

        return jsonify({
            'mensaje': 'Comentario eliminado exitosamente'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar comentario: {str(e)}'
        }), 500
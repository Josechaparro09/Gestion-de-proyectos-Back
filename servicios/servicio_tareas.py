# BACKEND servicios/servicio_tareas.py
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase
from flasgger import swag_from

task_bp = Blueprint('task', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')
USUARIOS = db.collection('usuarios')

@task_bp.route('/proyecto/<proyecto_id>/tareas', methods=['GET'])
def obtener_tareas(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        proyecto_data = proyecto.to_dict()
        tareas = proyecto_data.get('tareas', [])
        
        return jsonify(tareas)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@task_bp.route('/<proyecto_id>/tarea', methods=['POST'])
def crear_tarea(proyecto_id):
    try:
        print(f"Recibiendo solicitud para crear tarea en proyecto {proyecto_id}")
        datos = request.get_json()
        print("Datos recibidos:", datos)
        
        # Validar datos requeridos
        campos_requeridos = ['titulo', 'descripcion', 'fase', 'fecha_inicio', 'fecha_fin']
        for campo in campos_requeridos:
            if campo not in datos:
                return jsonify({'error': f'Falta el campo requerido: {campo}'}), 400

        nueva_tarea = {
            'id': str(datetime.now().timestamp()),
            'titulo': datos['titulo'],
            'descripcion': datos['descripcion'],
            'fase': datos['fase'],
            'asignado_a': datos.get('asignado_a'),  # Mantener como opcional
            'fecha_inicio': datos['fecha_inicio'],
            'fecha_fin': datos['fecha_fin'],
            'estado': 'pendiente',
            'fecha_creacion': str(datetime.now()),
            'comentarios': []
        }

        # Obtener el proyecto y sus tareas actuales
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        proyecto_data = proyecto.to_dict()
        tareas_actuales = proyecto_data.get('tareas', [])
        
        # Añadir la nueva tarea
        tareas_actuales.append(nueva_tarea)
        
        # Actualizar el proyecto con la nueva lista de tareas
        proyecto_ref.update({
            'tareas': tareas_actuales
        })
        
        return jsonify({
            'mensaje': 'Tarea creada exitosamente',
            'tarea': nueva_tarea
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@task_bp.route('/<proyecto_id>/tarea/<tarea_id>', methods=['PUT'])
def actualizar_tarea(proyecto_id, tarea_id):
    try:
        datos = request.get_json()
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        proyecto_data = proyecto.to_dict()
        tareas = proyecto_data.get('tareas', [])
        
        # Encontrar y actualizar la tarea
        for i, tarea in enumerate(tareas):
            if tarea.get('id') == tarea_id:
                tareas[i].update(datos)
                break
        
        # Actualizar el proyecto con las tareas modificadas
        proyecto_ref.update({
            'tareas': tareas
        })
        
        return jsonify({
            'mensaje': 'Tarea actualizada exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@task_bp.route('/<proyecto_id>/tarea/<tarea_id>', methods=['DELETE'])
def eliminar_tarea(proyecto_id, tarea_id):
    try:
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        proyecto_data = proyecto.to_dict()
        tareas = proyecto_data.get('tareas', [])
        
        # Filtrar la tarea a eliminar
        tareas_actualizadas = [t for t in tareas if t.get('id') != tarea_id]
        
        # Actualizar el proyecto con las tareas filtradas
        proyecto_ref.update({
            'tareas': tareas_actualizadas
        })
        
        return jsonify({
            'mensaje': 'Tarea eliminada exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@task_bp.route('/<proyecto_id>/tarea/<tarea_id>/comentario', methods=['POST'])
@swag_from({
    'tags': ['Tareas'],
    'summary': 'Agregar comentario a una tarea',
    'description': 'Agrega un nuevo comentario a una tarea específica',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto'
        },
        {
            'name': 'tarea_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID de la tarea'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'texto': {'type': 'string', 'description': 'Contenido del comentario'},
                    'autor_id': {'type': 'string', 'description': 'ID del autor del comentario'}
                },
                'required': ['texto', 'autor_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Comentario agregado exitosamente'
        },
        400: {
            'description': 'Error en la solicitud'
        },
        404: {
            'description': 'Proyecto o tarea no encontrado'
        }
    }
})
def agregar_comentario_tarea(proyecto_id, tarea_id):
    try:
        datos = request.get_json()
        texto = datos.get('texto')
        autor_id = datos.get('autor_id')

        # Validaciones
        if not texto or not autor_id:
            return jsonify({'error': 'Se requiere texto y autor_id'}), 400

        # Obtener información del autor
        autor = USUARIOS.document(autor_id).get()
        if not autor.exists:
            return jsonify({'error': 'Autor no encontrado'}), 404

        autor_data = autor.to_dict()

        # Crear el nuevo comentario
        nuevo_comentario = {
            'texto': texto,
            'autor': {
                'id': autor_id,
                'nombre': autor_data.get('nombre'),
                'rol': autor_data.get('rol')
            },
            'fecha': datetime.now().isoformat()
        }

        # Obtener el proyecto y sus tareas
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        tareas = proyecto_data.get('tareas', [])

        # Encontrar y actualizar la tarea específica
        tarea_encontrada = False
        for i, tarea in enumerate(tareas):
            if str(tarea.get('id')) == str(tarea_id):
                if 'comentarios' not in tarea:
                    tarea['comentarios'] = []
                tarea['comentarios'].append(nuevo_comentario)
                tarea_encontrada = True
                break

        if not tarea_encontrada:
            return jsonify({'error': 'Tarea no encontrada'}), 404

        # Actualizar el proyecto
        proyecto_ref.update({
            'tareas': tareas
        })

        return jsonify({
            'mensaje': 'Comentario agregado exitosamente',
            'comentario': nuevo_comentario
        })

    except Exception as e:
        print(f"Error en agregar_comentario_tarea: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    try:
        print(f"Añadiendo comentario a tarea {tarea_id} en proyecto {proyecto_id}")
        datos = request.get_json()
        autor_id = datos.get('autor_id')
        print(f"Datos recibidos: {datos}")

        # Obtener la información completa del autor
        autor = USUARIOS.document(autor_id).get()
        if not autor.exists:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        autor_data = autor.to_dict()
        
        nuevo_comentario = {
            'id': str(datetime.now().timestamp()),
            'texto': datos.get('texto'),
            'autor': autor_data,
            'fecha': str(datetime.now())
        }
        
        # Obtener el proyecto específico
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
            
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        proyecto_data = proyecto.to_dict()
        tareas = proyecto_data.get('tareas', [])
            
        # Encontrar y actualizar la tarea específica
        tarea_encontrada = False
        for i, tarea in enumerate(tareas):
            if str(tarea.get('id')) == str(tarea_id):
                if 'comentarios' not in tarea:
                    tarea['comentarios'] = []
                tarea['comentarios'].append(nuevo_comentario)
                tarea_encontrada = True
                break
                
        if not tarea_encontrada:
            return jsonify({'error': 'Tarea no encontrada'}), 404
                    
        # Actualizar el proyecto
        proyecto_ref.update({
            'tareas': tareas
        })
                    
        return jsonify({
            'mensaje': 'Comentario agregado exitosamente',
            'comentario': nuevo_comentario
        })

    except Exception as e:
        print(f"Error en agregar_comentario_tarea: {str(e)}")
        return jsonify({'error': str(e)}), 400
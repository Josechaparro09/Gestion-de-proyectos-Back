#BACKEND servicios\servicio_programa.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from configuracion.firebase_config import inicializar_firebase
from datetime import datetime
from flasgger import swag_from

programa_bp = Blueprint('programa', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

# Schemas comunes para la documentación
proyecto_schema = {
    'type': 'object',
    'properties': {
        'titulo': {'type': 'string', 'description': 'Título del proyecto'},
        'descripcion': {'type': 'string', 'description': 'Descripción detallada del proyecto'},
        'fase': {'type': 'string', 'description': 'Fase actual del proyecto'},
        'estado': {'type': 'string', 'description': 'Estado actual del proyecto'},
        'fecha_inicio': {'type': 'string', 'format': 'date', 'description': 'Fecha de inicio del proyecto'},
        'fecha_fin': {'type': 'string', 'format': 'date', 'description': 'Fecha de finalización del proyecto'},
        'director_id': {'type': 'string', 'description': 'ID del director del proyecto'},
        'comentarios': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'texto': {'type': 'string'},
                    'fecha': {'type': 'string'},
                    'autor_id': {'type': 'string'}
                }
            }
        }
    }
}

@programa_bp.route('/proyectos', methods=['POST'])
@swag_from({
    'tags': ['Programa'],
    'summary': 'Crear nuevo proyecto',
    'description': 'Crea un nuevo proyecto en el sistema',
    'parameters': [
        {
            'name': 'proyecto',
            'in': 'body',
            'required': True,
            'schema': proyecto_schema
        }
    ],
    'responses': {
        200: {
            'description': 'Proyecto creado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'id': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Error en la solicitud',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def crear_proyecto():
    try:
        datos = request.get_json()
        
        # Validación básica de campos requeridos
        campos_requeridos = ['titulo', 'descripcion', 'fase', 'estado', 'fecha_inicio', 'director_id']
        for campo in campos_requeridos:
            if campo not in datos:
                return jsonify({'error': f'El campo {campo} es requerido'}), 400

        doc_ref = PROYECTOS.add({
            'titulo': datos['titulo'],
            'descripcion': datos['descripcion'],
            'fase': datos['fase'],
            'estado': datos['estado'],
            'fecha_inicio': datos['fecha_inicio'],
            'fecha_fin': datos.get('fecha_fin'),
            'director_id': datos['director_id'],
            'fecha_creacion': firestore.SERVER_TIMESTAMP,
            'comentarios': []
        })
        
        return jsonify({
            'mensaje': 'Proyecto creado exitosamente',
            'id': doc_ref[1].id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/proyectos', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Listar todos los proyectos',
    'description': 'Obtiene la lista de todos los proyectos registrados',
    'responses': {
        200: {
            'description': 'Lista de proyectos',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        **proyecto_schema['properties']
                    }
                }
            }
        }
    }
})
def listar_proyectos():
    try:
        proyectos = PROYECTOS.get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/proyectos/<proyecto_id>/progreso', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Ver progreso de un proyecto',
    'description': 'Obtiene los detalles y progreso de un proyecto específico',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID del proyecto'
        }
    ],
    'responses': {
        200: {
            'description': 'Detalles del proyecto',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    **proyecto_schema['properties']
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado'
        }
    }
})
def ver_progreso(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        return jsonify({
            'id': proyecto.id,
            **proyecto.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/proyectos/<proyecto_id>/comentario', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Agregar comentario a un proyecto',
    'description': 'Agrega un nuevo comentario a un proyecto específico',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID del proyecto'
        },
        {
            'name': 'comentario',
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
            'description': 'Comentario agregado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Error en la solicitud'
        }
    }
})
def agregar_comentario(proyecto_id):
    try:
        datos = request.get_json()
        
        # Validación de campos requeridos
        if not datos.get('texto') or not datos.get('autor_id'):
            return jsonify({'error': 'El texto y el autor_id son requeridos'}), 400

        comentario = {
            'texto': datos['texto'],
            'fecha': str(datetime.now()),
            'autor_id': datos['autor_id']
        }
        
        PROYECTOS.document(proyecto_id).update({
            'comentarios': firestore.ArrayUnion([comentario])
        })
        
        return jsonify({'mensaje': 'Comentario agregado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@programa_bp.route('/estadisticas', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener estadísticas de proyectos',
    'description': 'Obtiene estadísticas generales sobre los proyectos',
    'responses': {
        200: {
            'description': 'Estadísticas de proyectos',
            'schema': {
                'type': 'object',
                'properties': {
                    'total_proyectos': {'type': 'integer'},
                    'por_estado': {
                        'type': 'object',
                        'additionalProperties': {'type': 'integer'}
                    },
                    'por_fase': {
                        'type': 'object',
                        'additionalProperties': {'type': 'integer'}
                    }
                }
            }
        }
    }
})
def obtener_estadisticas():
    try:
        proyectos = PROYECTOS.get()
        datos = {
            'total_proyectos': 0,
            'por_estado': {},
            'por_fase': {}
        }
        
        for proyecto in proyectos:
            datos['total_proyectos'] += 1
            p = proyecto.to_dict()
            
            estado = p.get('estado', 'sin_estado')
            fase = p.get('fase', 'sin_fase')
            
            datos['por_estado'][estado] = datos['por_estado'].get(estado, 0) + 1
            datos['por_fase'][fase] = datos['por_fase'].get(fase, 0) + 1
        
        return jsonify(datos)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
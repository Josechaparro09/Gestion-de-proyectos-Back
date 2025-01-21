# BACKEND servicios\servicio_proyecto.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from flasgger import Swagger,swag_from
from configuracion.supabase_configuration import inicializar_supabase

proyecto_bp = Blueprint('proyecto', __name__)
db = inicializar_firebase()
supabase = inicializar_supabase()
PROYECTOS = db.collection('proyectos')
USUARIOS = db.collection('usuarios')
BUCKET_NAME = "archivos"  # Nombre del bucket
BASE_PATH = "proyectos"


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def es_fecha_pasada(fecha):
    if not fecha:
        return False
    try:
        fecha_entrega = datetime.strptime(fecha, '%Y-%m-%d')
        return fecha_entrega.date() <= datetime.now().date()
    except (ValueError, TypeError):
        return False

def calcular_avance_fase(datos_fase):
    # Calculamos avance basado en entregas
    total_entregas = len(datos_fase.get('entregas', []))
    entregas_completadas = sum(1 for e in datos_fase.get('entregas', []) 
                             if es_fecha_pasada(e.get('fecha_entrega')))
    
    # Calculamos avance basado en avances registrados
    total_avances = len(datos_fase.get('avances', []))
    
    # Calculamos el porcentaje combinando entregas y avances
    if total_entregas > 0:
        porcentaje_entregas = (entregas_completadas / total_entregas) * 50
    else:
        porcentaje_entregas = 0
        
    if total_avances > 0:
        porcentaje_avances = 50
    else:
        porcentaje_avances = 0
        
    porcentaje_total = porcentaje_entregas + porcentaje_avances
    obtener_avance_proyecto
    # Si la fase está marcada como completada, el porcentaje es 100%
    if datos_fase.get('completada', False):
        porcentaje_total = 100

    return {
        "porcentaje_completado": porcentaje_total,
        "entregas": {
            "total": total_entregas,
            "completadas": entregas_completadas
        },
        "avances": {
            "total": total_avances,
            "registros": datos_fase.get('avances', [])
        },
        "completada": datos_fase.get('completada', False)
    }
   
   
   
# @proyecto_bp.route('/<proyecto_id>/archivo', methods=['POST'])
# def subir_archivo_proyecto(proyecto_id):
    try:
        if 'archivo' not in request.files:
            return jsonify({'error': 'No se envió ningún archivo'}), 400
            
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
            
        if archivo and allowed_file(archivo.filename):
            # Generar nombre único para el archivo
            filename = secure_filename(archivo.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Crear ruta en Supabase - siguiendo la estructura archivos/proyectos/[proyecto_id]/
            file_path = f"{BASE_PATH}/{proyecto_id}/{unique_filename}"
            
            # Subir archivo a Supabase
            response = supabase.storage \
                .from_(BUCKET_NAME) \
                .upload(file_path, archivo.read())
            
            if response.error:
                return jsonify({'error': 'Error al subir el archivo'}), 400
                
            # Obtener URL pública del archivo
            file_url = supabase.storage \
                .from_(BUCKET_NAME) \
                .get_public_url(file_path)
            
            # Crear metadata del archivo
            metadata = {
                'nombre_original': filename,
                'nombre_storage': unique_filename,
                'ruta': file_path,
                'url': file_url,
                'tipo': archivo.content_type,
                'fecha_subida': str(datetime.now()),
                'subido_por': request.form.get('usuario_id')
            }
            
            # Actualizar documento del proyecto con la información del archivo
            PROYECTOS.document(proyecto_id).update({
                'archivos': firestore.ArrayUnion([metadata])
            })
            
            return jsonify({
                'mensaje': 'Archivo subido exitosamente',
                'metadata': metadata
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/entrega/archivo', methods=['POST'])
@swag_from({
    'tags': ['Entregas'],
    'summary': 'Crear una nueva entrega con archivo',
    'description': 'Endpoint para crear una nueva entrega en una fase de proyecto, con la opción de subir un archivo.',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID del proyecto'
        },
        {
            'name': 'fase',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre de la fase'
        },
        {
            'name': 'titulo',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Título de la entrega'
        },
        {
            'name': 'descripcion',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Descripción de la entrega'
        },
        {
            'name': 'fecha_entrega',
            'in': 'formData',
            'type': 'string',
            'format': 'date',
            'required': True,
            'description': 'Fecha límite de la entrega'
        },
        {
            'name': 'archivo',
            'in': 'formData',
            'type': 'file',
            'required': False,
            'description': 'Archivo de la entrega'
        }
    ],
    'responses': {
        200: {
            'description': 'Entrega creada exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'entrega': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'titulo': {'type': 'string'},
                            'descripcion': {'type': 'string'},
                            'fecha_entrega': {'type': 'string', 'format': 'date'},
                            'archivo': {
                                'type': 'object',
                                'properties': {
                                    'nombre_original': {'type': 'string'},
                                    'nombre_storage': {'type': 'string'},
                                    'ruta_storage': {'type': 'string'},
                                    'url': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Error al crear la entrega',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def subir_archivo_entrega(proyecto_id, fase):
    try:
        # Validar campos requeridos
        print("Headers recibidos:", request.headers)
        print("Contenido de form:", request.form)
        print("Archivos recibidos:", request.files)

        # Validaciones más estrictas
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion', '')
        fecha_entrega = request.form.get('fecha_entrega')
        
        if not titulo:
            return jsonify({'error': 'El título es obligatorio'}), 400
        
        if not fecha_entrega:
            return jsonify({'error': 'La fecha de entrega es obligatoria'}), 400

        # Metadata para la entrega
        metadata_archivo = None
        
        # Manejo del archivo (opcional)
        if 'archivo' in request.files:
            archivo = request.files['archivo']
            
            if archivo.filename:
                # Utilizar la función de subida de archivos con Supabase
                metadata_archivo = subir_archivo_supabase(
                    archivo, 
                    proyecto_id, 
                    subcarpeta=f'entregas/{fase}',
                    usuario_id=request.form.get('usuario_id')
                )
        
        # Crear objeto de entrega
        entrega = {
            'id': str(datetime.now().timestamp()),
            'titulo': titulo,
            'descripcion': descripcion,
            'fecha_entrega': fecha_entrega,
            'fecha_creacion': str(datetime.now()),
            'archivo': metadata_archivo
        }
        
        # Actualizar proyecto en Firestore
        PROYECTOS.document(proyecto_id).update({
            f'fases.{fase}.entregas': firestore.ArrayUnion([entrega])
        })
        
        return jsonify({
            'mensaje': 'Entrega creada exitosamente',
            'entrega': entrega
        }), 200
    
    except Exception as e:
        # Loggear el error para depuración
        print(f"Error al crear entrega: {str(e)}")
        return jsonify({
            'error': f'Error al crear la entrega: {str(e)}'
        }), 400
    
    
# @proyecto_bp.route('/<proyecto_id>/archivo/<filename>', methods=['DELETE'])
# def eliminar_archivo_proyecto(proyecto_id, filename):
#     try:
#         # Path completo para eliminar archivo
#         file_path = f"{BASE_PATH}/{proyecto_id}/{filename}"
        
#         # Eliminar archivo de Supabase
#         response = supabase.storage \
#             .from_(BUCKET_NAME) \
#             .remove([file_path])
            
#         if response.error:
#             return jsonify({'error': 'Error al eliminar el archivo'}), 400
            
#         # Actualizar documento del proyecto
#         proyecto = PROYECTOS.document(proyecto_id).get().to_dict()
#         archivos = proyecto.get('archivos', [])
#         archivos = [a for a in archivos if a['nombre_storage'] != filename]
        
#         PROYECTOS.document(proyecto_id).update({
#             'archivos': archivos
#         })
        
#         return jsonify({
#             'mensaje': 'Archivo eliminado exitosamente'
#         })
#     except Exception as e:
#         return jsonify({'error': str(e)}), 400
    
@proyecto_bp.route('/<proyecto_id>/archivos', methods=['GET'])
def obtener_archivos_proyecto(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        archivos = proyecto.to_dict().get('archivos', [])
        
        # Verificar y actualizar URLs si es necesario
        archivos_actualizados = []
        for archivo in archivos:
            # Renovar URL pública si es necesario
            file_url = supabase.storage \
                .from_(BUCKET_NAME) \
                .get_public_url(archivo['ruta'])
                
            archivo['url'] = file_url
            archivos_actualizados.append(archivo)
            
        return jsonify(archivos_actualizados)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/crear', methods=['POST'])
@swag_from({
   "tags": ["Proyectos"],
   "description": "Crea un nuevo proyecto",
   "parameters": [
       {
           "name": "body",
           "in": "body",
           "schema": {
               "type": "object",
               "required": ["titulo", "descripcion", "fecha_inicio", "fecha_fin", "lider_id"],
               "properties": {
                   "titulo": {"type": "string", "description": "Título del proyecto"},
                   "descripcion": {"type": "string", "description": "Descripción detallada"},
                   "fecha_inicio": {"type": "string", "format": "date", "description": "Fecha de inicio (YYYY-MM-DD)"},
                   "fecha_fin": {"type": "string", "format": "date", "description": "Fecha de finalización (YYYY-MM-DD)"},
                   "lider_id": {"type": "string", "description": "ID del líder del proyecto"},
                   "docente_id": {"type": "string", "description": "ID del docente guía (opcional)"},
                   "colaboradores_id": {"type": "string", "description": "ID del colaborador (opcional)"},
                   "facultad": {"type": "string", "description": "Facultad académica (opcional)"},
                   "carrera": {"type": "string", "description": "Carrera académica (opcional)"}
               }
           }
       }
   ],
   "responses": {
       "201": {
           "description": "Proyecto creado exitosamente",
           "schema": {
               "type": "object",
               "properties": {
                   "mensaje": {"type": "string"},
                   "id": {"type": "string"},
                   "proyecto": {"type": "object"}
               }
           }
       },
       "400": {
           "description": "Error de validación",
           "schema": {
               "type": "object",
               "properties": {
                   "error": {"type": "string"}
               }
           }
       },
       "404": {
           "description": "Docente o colaborador no encontrado",
           "schema": {
               "type": "object", 
               "properties": {
                   "error": {"type": "string"}
               }
           }
       }
   }
})

def crear_proyecto():
    try:
        datos = request.get_json()
        
        # Validate required fields
        required_fields = ['titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'lider_id']
        for field in required_fields:
            if not datos.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400

        
        
        # Validate docente if provided
        docente_data = None
        if datos.get('docente_id'):
            docente_ref = USUARIOS.document(datos.get('docente_id')).get()
            if not docente_ref.exists:
                return jsonify({'error': 'Docente no encontrado'}), 404
            docente_data = docente_ref.to_dict()
            docente_data['uid'] = docente_ref.id

        # Validate colaborador if provided
        lider_data = None
        if datos.get('lider_id'):
            lider_ref = USUARIOS.document(datos.get('lider_id')).get()
            if not lider_ref.exists:
                return jsonify({'error': 'Líder no encontrado'}), 404
            lider_data = lider_ref.to_dict()
            lider_data['uid'] = lider_ref.id

        # Create project with proper structure
        proyecto_data = {
            'titulo': datos['titulo'],
            'descripcion': datos['descripcion'],
            'fases': {
                'planificacion': {
                    'completada': False,
                    'entregas': [],
                    'fecha_inicio': None,
                    'fecha_fin': None
                },
                'desarrollo': {
                    'completada': False,
                    'entregas': [],
                    'fecha_inicio': None,
                    'fecha_fin': None
                },
                'evaluacion': {
                    'completada': False,
                    'entregas': [],
                    'fecha_inicio': None,
                    'fecha_fin': None
                }
            },
            'estado': 'activo',
            'fecha_inicio': datos['fecha_inicio'],
            'fecha_fin': datos['fecha_fin'],
            'fecha_creacion': str(datetime.now()),
            'lider_id': datos['lider_id'],
            'lider': lider_data,
            'docente_id': datos.get('docente_id'),
            'docente': docente_data,
            'colaboradores': datos['colaboradores'],
            'facultad': datos.get('facultad'),
            'carrera': datos.get('carrera'),
            'tareas': [],
            'comentarios': [],
            'archivos': []
        }

        doc_ref = PROYECTOS.add(proyecto_data)
        
        return jsonify({
            'mensaje': 'Proyecto creado exitosamente',
            'id': doc_ref[1].id,
            'proyecto': proyecto_data
        }), 201

    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return jsonify({'error': f'Error al crear el proyecto: {str(e)}'}), 400
    
    
@proyecto_bp.route('/<proyecto_id>', methods=['PUT'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Actualizar un proyecto existente',
    'description': 'Este endpoint permite actualizar la información de un proyecto existente.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto a actualizar'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'titulo': {'type': 'string', 'description': 'Nuevo título del proyecto'},
                    'descripcion': {'type': 'string', 'description': 'Nueva descripción del proyecto'},
                    'fecha_inicio': {'type': 'string', 'format': 'date', 'description': 'Nueva fecha de inicio'},
                    'fecha_fin': {'type': 'string', 'format': 'date', 'description': 'Nueva fecha de fin'},
                    'estado': {'type': 'string', 'description': 'Nuevo estado del proyecto'},
                    'facultad': {'type': 'string', 'description': 'Nueva facultad del proyecto'},
                    'carrera': {'type': 'string', 'description': 'Nueva carrera del proyecto'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Proyecto actualizado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'proyecto': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'titulo': {'type': 'string'},
                            'descripcion': {'type': 'string'},
                            'fecha_inicio': {'type': 'string'},
                            'fecha_fin': {'type': 'string'},
                            'estado': {'type': 'string'},
                            'facultad': {'type': 'string'},
                            'carrera': {'type': 'string'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
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
def actualizar_proyecto(proyecto_id):
    try:
        datos = request.get_json()
        
        # Verificar si el proyecto existe
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        # Actualizar solo los campos proporcionados
        campos_actualizables = [
            'titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 
            'estado', 'facultad', 'carrera'
        ]
        
        actualizaciones = {}
        for campo in campos_actualizables:
            if campo in datos:
                actualizaciones[campo] = datos[campo]
        
        if not actualizaciones:
            return jsonify({'error': 'No se proporcionaron campos para actualizar'}), 400
            
        # Realizar la actualización
        proyecto_ref.update(actualizaciones)
        
        # Obtener el proyecto actualizado
        proyecto_actualizado = proyecto_ref.get().to_dict()
        
        return jsonify({
            'mensaje': 'Proyecto actualizado exitosamente',
            'proyecto': {
                'id': proyecto_id,
                **proyecto_actualizado
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@proyecto_bp.route('/proyecto/<proyecto_id>/nueva-tarea', methods=['POST'])
@swag_from({
    'tags': ['Tareas'],
    'summary': 'Crear una nueva tarea en un proyecto',
    'description': 'Este endpoint permite crear una tarea y asociarla a un proyecto existente.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto al que se asignará la tarea.'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'titulo': {'type': 'string', 'description': 'El título de la tarea'},
                    'descripcion': {'type': 'string', 'description': 'La descripción de la tarea'},
                    'asignado_a': {'type': 'string', 'description': 'El ID del usuario al que se asigna la tarea'},
                    'fecha_inicio': {'type': 'string', 'format': 'date', 'description': 'La fecha de inicio de la tarea'},
                    'fecha_fin': {'type': 'string', 'format': 'date', 'description': 'La fecha de finalización de la tarea'}
                },
                'required': ['titulo', 'fecha_inicio', 'fecha_fin']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Tarea creada exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'tarea': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'titulo': {'type': 'string'},
                            'descripcion': {'type': 'string'},
                            'asignado_a': {'type': 'string'},
                            'fecha_inicio': {'type': 'string', 'format': 'date'},
                            'fecha_fin': {'type': 'string', 'format': 'date'},
                            'estado': {'type': 'string'},
                            'fecha_creacion': {'type': 'string', 'format': 'date-time'},
                            'comentarios_docente': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Error al crear la tarea',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def crear_tarea(proyecto_id):
    try:
        datos = request.get_json()
        tarea = {
            'id': str(datetime.now().timestamp()),  # Agregar ID único
            'titulo': datos.get('titulo'),
            'descripcion': datos.get('descripcion'),
            'asignado_a': datos.get('asignado_a'),
            'fecha_inicio': datos.get('fecha_inicio'),
            'fecha_fin': datos.get('fecha_fin'),
            'estado': 'pendiente',
            'fecha_creacion': str(datetime.now()),
            'comentarios_docente': []
        }
        
        PROYECTOS.document(proyecto_id).update({
            'tareas': firestore.ArrayUnion([tarea])
        })
        
        return jsonify({'mensaje': 'Tarea creada exitosamente', 'tarea': tarea})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/docente', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Asignar un docente a un proyecto',
    'description': 'Este endpoint permite asignar un docente guía a un proyecto especificado.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto al que se asignará el docente.'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'docente_id': {'type': 'string', 'description': 'El ID del docente guía que se asignará al proyecto'}
                },
                'required': ['docente_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Docente asignado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Error al asignar docente',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def asignar_docente(proyecto_id):
   try:
       datos = request.get_json()
       docente_id = datos.get('docente_id')
       
       # Verificar que el docente existe y es docente
       docente = USUARIOS.document(docente_id).get()
       if not docente.exists or docente.get('rol') != 'docente_guia':
           return jsonify({'error': 'Docente no válido'}), 400
           
       PROYECTOS.document(proyecto_id).update({
           'docente_id': docente_id
       })
       
       return jsonify({'mensaje': 'Docente asignado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/tarea', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'tarea',
            'in': 'body',
            'required': True,
            'schema': {
                'id': 'Tarea',
                'required': ['titulo', 'descripcion', 'asignado_a'],
                'properties': {
                    'titulo': {'type': 'string'},
                    'descripcion': {'type': 'string'},
                    'asignado_a': {'type': 'string'},
                    'fecha_inicio': {'type': 'string', 'format': 'date'},
                    'fecha_fin': {'type': 'string', 'format': 'date'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Tarea creada exitosamente'},
        400: {'description': 'Error en la solicitud'}
    }
})
def crear_tarea_fase(proyecto_id, fase):
    try:
        datos = request.get_json()
        
        nueva_tarea = {
            'id': str(datetime.now().timestamp()),
            'titulo': datos.get('titulo'),
            'descripcion': datos.get('descripcion'),
            'asignado_a': datos.get('asignado_a'),
            'fecha_inicio': datos.get('fecha_inicio'),
            'fecha_fin': datos.get('fecha_fin'),
            'estado': 'pendiente',
            'fase': fase,
            'fecha_creacion': str(datetime.now())
        }
        
        # Actualizar el documento del proyecto
        PROYECTOS.document(proyecto_id).update({
            f'fases.{fase}.tareas': firestore.ArrayUnion([nueva_tarea])
        })
        
        return jsonify({
            'mensaje': 'Tarea creada exitosamente',
            'tarea': nueva_tarea
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/tarea/<tarea_id>', methods=['PUT'])
@swag_from({
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID único del proyecto'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase (planificacion, desarrollo, evaluacion)',
            'enum': ['planificacion', 'desarrollo', 'evaluacion']
        },
        {
            'name': 'tarea_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID único de la tarea'
        },
        {
            'name': 'tarea',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'titulo': {
                        'type': 'string',
                        'description': 'Nuevo título de la tarea'
                    },
                    'descripcion': {
                        'type': 'string',
                        'description': 'Nueva descripción de la tarea'
                    },
                    'estado': {
                        'type': 'string',
                        'enum': ['pendiente', 'en_progreso', 'completada'],
                        'description': 'Nuevo estado de la tarea'
                    },
                    'asignado_a': {
                        'type': 'string',
                        'description': 'ID del colaborador asignado'
                    },
                    'fecha_inicio': {
                        'type': 'string',
                        'format': 'date',
                        'description': 'Nueva fecha de inicio'
                    },
                    'fecha_fin': {
                        'type': 'string',
                        'format': 'date',
                        'description': 'Nueva fecha de fin'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Tarea actualizada exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {
                        'type': 'string',
                        'example': 'Tarea actualizada exitosamente'
                    },
                    'tarea': {
                        '$ref': '#/definitions/Tarea'
                    }
                }
            }
        },
        404: {
            'description': 'Tarea no encontrada',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Tarea no encontrada'
                    }
                }
            }
        },
        400: {
            'description': 'Error en la solicitud',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'Error al actualizar la tarea'
                    }
                }
            }
        }
    },
    'tags': ['Tareas']
})
def actualizar_tarea_fase(proyecto_id, fase, tarea_id):
    try:
        datos = request.get_json()
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get().to_dict()
        
        tareas = proyecto['fases'][fase].get('tareas', [])
        tarea_index = next((index for (index, t) in enumerate(tareas) if t['id'] == tarea_id), None)
        
        if tarea_index is not None:
            tareas[tarea_index].update(datos)
            proyecto_ref.update({
                f'fases.{fase}.tareas': tareas
            })
            return jsonify({
                'mensaje': 'Tarea actualizada exitosamente',
                'tarea': tareas[tarea_index]
            })
        else:
            return jsonify({'error': 'Tarea no encontrada'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/tarea/<tarea_id>', methods=['DELETE'])
def eliminar_tarea_fase(proyecto_id, fase, tarea_id):
    try:
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get().to_dict()
        
        tareas = proyecto['fases'][fase].get('tareas', [])
        tareas = [t for t in tareas if t['id'] != tarea_id]
        
        proyecto_ref.update({
            f'fases.{fase}.tareas': tareas
        })
        
        return jsonify({'mensaje': 'Tarea eliminada exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/colaborador', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Asignar un colaborador a un proyecto',
    'description': 'Este endpoint permite asignar un colaborador a un proyecto especificado.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto al que se asignará el colaborador.'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'colaborador_id': {'type': 'string', 'description': 'El ID del colaborador que se asignará al proyecto'}
                },
                'required': ['colaborador_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Colaborador asignado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Error al asignar colaborador',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def asignar_colaborador(proyecto_id):
   try:
       datos = request.get_json()
       colaborador_id = datos.get('colaborador_id')
       
       # Verificar que el colaborador existe
       colaborador = USUARIOS.document(colaborador_id).get()
       if not colaborador.exists or colaborador.get('rol') != 'colaborador':
           return jsonify({'error': 'Colaborador no válido'}), 400
           
       PROYECTOS.document(proyecto_id).update({
           'colaboradores': firestore.ArrayUnion([colaborador_id])
       })
       
       return jsonify({'mensaje': 'Colaborador asignado exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400
   
# Función para obtener el progreso de un proyecto
@proyecto_bp.route('/<proyecto_id>/avance', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener el avance de un proyecto',
    'description': 'Este endpoint permite calcular y devolver el avance general y por fase de un proyecto específico.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto cuyo avance se desea consultar.'
        }
    ],
    'responses': {
        200: {
            'description': 'Avance del proyecto obtenido exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'avance_general': {'type': 'number', 'format': 'float', 'description': 'El avance general del proyecto en porcentaje.'},
                    'avance_por_fase': {
                        'type': 'object',
                        'additionalProperties': {
                            'type': 'object',
                            'properties': {
                                'porcentaje_completado': {'type': 'number', 'description': 'El porcentaje completado de la fase.'},
                                'otros_datos': {'type': 'object', 'description': 'Otros datos relacionados con la fase (si aplica).'}
                            }
                        }
                    },
                    'total_fases': {'type': 'integer', 'description': 'El total de fases en el proyecto.'},
                    'fases_completadas': {'type': 'integer', 'description': 'El número de fases completadas.'}
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Error al obtener el avance del proyecto',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def obtener_avance_proyecto(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        proyecto_data = proyecto.to_dict()
        avance_por_fase = {}

        # Calculamos el progreso de cada fase
        for fase_nombre, datos_fase in proyecto_data['fases'].items():
            avance_por_fase[fase_nombre] = calcular_avance_fase(datos_fase)

        # Calculamos el avance general del proyecto
        avance_general = sum(fase["porcentaje_completado"] for fase in avance_por_fase.values()) / len(proyecto_data['fases'])

        respuesta = {
            'avance_general': avance_general,
            'avance_por_fase': avance_por_fase,
            'total_fases': len(proyecto_data['fases']),
            'fases_completadas': sum(1 for fase in proyecto_data['fases'].values() if fase.get('completada', False))
        }

        return jsonify(respuesta), 200
    
    except Exception as e:
        print(f"Error en obtener_avance_proyecto: {str(e)}")
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/entrega', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Agregar una entrega a una fase de un proyecto',
    'description': 'Este endpoint permite agregar una entrega a una fase específica de un proyecto.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto donde se agregará la entrega.'
        },
        {
            'name': 'fase',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El nombre de la fase donde se agregará la entrega.'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'description': 'Datos de la entrega que se va a agregar.',
            'schema': {
                'type': 'object',
                'properties': {
                    'titulo': {'type': 'string', 'description': 'Título de la entrega.', 'example': 'Entrega inicial'},
                    'fecha_entrega': {'type': 'string', 'format': 'date', 'description': 'Fecha de entrega.', 'example': '2024-12-15'},
                    'archivo': {'type': 'string', 'description': 'Ruta o enlace del archivo asociado a la entrega.', 'example': 'https://example.com/archivo.pdf'}
                },
                'required': ['titulo', 'fecha_entrega']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Entrega agregada exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'entrega': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'description': 'ID único de la entrega.'},
                            'titulo': {'type': 'string', 'description': 'Título de la entrega.'},
                            'fecha_entrega': {'type': 'string', 'format': 'date', 'description': 'Fecha de entrega.'},
                            'archivo': {'type': 'string', 'description': 'Ruta o enlace del archivo asociado.'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
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
def agregar_entrega(proyecto_id, fase):
    try:
        # Verificar si la fase existe
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        proyecto_data = proyecto.to_dict()
        
        if fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400
        
        # Obtener los datos de la entrega
        datos = request.get_json()
        entrega = {
            'id': str(datetime.now().timestamp()),  # ID único
            'titulo': datos.get('titulo'),
            'fecha_entrega': datos.get('fecha_entrega'),
            'archivo': datos.get('archivo')  # Si se sube un archivo, se maneja aquí
        }
        
        # Agregar la entrega a la fase correspondiente
        PROYECTOS.document(proyecto_id).update({
            f'fases.{fase}.entregas': firestore.ArrayUnion([entrega])
        })
        
        return jsonify({'mensaje': 'Entrega agregada exitosamente', 'entrega': entrega}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/completar', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Completar una fase de un proyecto',
    'description': 'Este endpoint permite marcar una fase específica de un proyecto como completada, verificando las condiciones necesarias para hacerlo.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID del proyecto donde se encuentra la fase.'
        },
        {
            'name': 'fase',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El nombre de la fase que se desea completar.'
        }
    ],
    'responses': {
        200: {
            'description': 'Fase completada exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'fase': {'type': 'string'},
                    'estado': {'type': 'string', 'example': 'completada'}
                }
            }
        },
        400: {
            'description': 'Error en la solicitud o entregas pendientes',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'fase': {'type': 'string'},
                    'estado': {'type': 'string', 'example': 'pendiente'},
                    'entregas_pendientes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'titulo': {'type': 'string'},
                                'fecha_entrega': {'type': 'string', 'format': 'date'}
                            }
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto o fase no encontrada',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def completar_fase(proyecto_id, fase):
    try:
        # Verificar si el proyecto existe
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()

        # Verificar que la fase sea válida
        if fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400

        datos_fase = proyecto_data['fases'][fase]

        # Verificar si la fase ya está completada
        if datos_fase.get('completada', False):
            return jsonify({'mensaje': f'La fase {fase} ya está completada'}), 200

        # Obtenemos las entregas de la fase
        entregas = datos_fase.get('entregas', [])

        if not entregas:
            # Si no hay entregas, completamos la fase directamente
            proyecto_ref.update({
                f'fases.{fase}.completada': True
            })
            return jsonify({
                'mensaje': f'Fase {fase} completada exitosamente',
                'fase': fase,
                'estado': 'completada'
            }), 200

        # Verificamos las fechas de entrega si hay entregas
        entregas_pendientes = []
        for entrega in entregas:
            fecha_entrega = entrega.get('fecha_entrega')
            if fecha_entrega and not es_fecha_pasada(fecha_entrega):
                entregas_pendientes.append({
                    'titulo': entrega.get('titulo'),
                    'fecha_entrega': fecha_entrega
                })

        if entregas_pendientes:
            return jsonify({
                'error': f'No todas las entregas de la fase {fase} han sido completadas',
                'fase': fase,
                'estado': 'pendiente',
                'entregas_pendientes': entregas_pendientes
            }), 400

        # Si llegamos aquí, podemos completar la fase
        proyecto_ref.update({
            f'fases.{fase}.completada': True
        })

        return jsonify({
            'mensaje': f'Fase {fase} completada exitosamente',
            'fase': fase,
            'estado': 'completada'
        }), 200

    except Exception as e:
        print(f"Error en completar_fase: {str(e)}")
        return jsonify({
            'error': str(e),
            'fase': fase,
            'estado': 'error'
        }), 400
        
@proyecto_bp.route('/<proyecto_id>', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener un proyecto por ID',
    'description': 'Este endpoint permite obtener los detalles completos de un proyecto especificado mediante su ID.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'El ID único del proyecto que se desea obtener.'
        }
    ],
    'responses': {
        200: {
            'description': 'Detalles del proyecto obtenidos exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'proyecto': {
                        'type': 'object',
                        'description': 'Datos completos del proyecto',
                        'additionalProperties': True
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
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
def obtener_proyecto(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        return jsonify({'proyecto': proyecto_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/proyectos', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener todos los proyectos',
    'description': 'Este endpoint permite obtener una lista de todos los proyectos registrados en el sistema.',
    'responses': {
        200: {
            'description': 'Lista de proyectos obtenida exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'proyectos': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'description': 'Datos completos de cada proyecto',
                            'properties': {
                                'id': {'type': 'string', 'description': 'ID del proyecto'},
                                'titulo': {'type': 'string', 'description': 'Título del proyecto'},
                                'descripcion': {'type': 'string', 'description': 'Descripción del proyecto'},
                                'fecha_inicio': {'type': 'string', 'format': 'date-time', 'description': 'Fecha de inicio del proyecto'},
                                'fecha_fin': {'type': 'string', 'format': 'date-time', 'description': 'Fecha de fin del proyecto'},
                                'estado': {'type': 'string', 'description': 'Estado del proyecto'},
                                # Agregar otros campos relevantes del proyecto aquí
                            }
                        }
                    }
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

def obtener_proyectos():
    try:
        proyectos = PROYECTOS.stream()  # Obtener todos los documentos de la colección
        lista_proyectos = [{**doc.to_dict(), 'id': doc.id} for doc in proyectos]
        
        return jsonify({'proyectos': lista_proyectos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@proyecto_bp.route('/lider/<lider_id>', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener proyectos del líder',
    'description': 'Este endpoint permite obtener todos los proyectos asociados a un líder específico.',
    'parameters': [
        {
            'name': 'lider_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del líder para obtener los proyectos que lidera'
        }
    ],
    'responses': {
        200: {
            'description': 'Proyectos del líder obtenidos exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'proyectos': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string', 'description': 'ID del proyecto'},
                                'titulo': {'type': 'string', 'description': 'Título del proyecto'},
                                'descripcion': {'type': 'string', 'description': 'Descripción del proyecto'},
                                'fecha_inicio': {'type': 'string', 'format': 'date-time', 'description': 'Fecha de inicio del proyecto'},
                                'fecha_fin': {'type': 'string', 'format': 'date-time', 'description': 'Fecha de fin del proyecto'},
                                'estado': {'type': 'string', 'description': 'Estado del proyecto'},
                                # Agregar otros campos relevantes del proyecto aquí
                            }
                        }
                    },
                    'total': {'type': 'integer', 'description': 'Número total de proyectos del líder'}
                }
            }
        },
        404: {
            'description': 'Líder no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
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
def obtener_proyectos_lider(lider_id):
    try:
        # Verificar que el líder existe
        lider = USUARIOS.document(lider_id).get()
        if not lider.exists:
            return jsonify({'error': 'Líder no encontrado'}), 404
            
        # Obtener todos los proyectos donde el usuario es líder
        proyectos = PROYECTOS.where('lider_id', '==', lider_id).stream()
        
        # Convertir los proyectos a una lista de diccionarios
        proyectos_data = []
        for proyecto in proyectos:
            data = proyecto.to_dict()
            data['id'] = proyecto.id  # Agregar el ID del documento
            proyectos_data.append(data)
            
        return jsonify({
            'proyectos': proyectos_data,
            'total': len(proyectos_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    
    # Endpoint para ver el avance general del proyecto

# Endpoint para ver el avance de una fase específica

@proyecto_bp.route('/<proyecto_id>/fase/<fase>/avance', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener avance de una fase de un proyecto',
    'description': 'Este endpoint permite obtener el avance de una fase específica de un proyecto.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto del cual se quiere obtener el avance de la fase'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase para la cual se desea obtener el avance'
        }
    ],
    'responses': {
        200: {
            'description': 'Avance de la fase obtenido exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'nombre_fase': {'type': 'string', 'description': 'Nombre de la fase'},
                    'avance': {'type': 'number', 'description': 'Porcentaje de avance de la fase', 'format': 'float'}
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        400: {
            'description': 'Fase no válida o error en la solicitud',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def obtener_avance_fase(proyecto_id, fase):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        if fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400

        datos_fase = proyecto_data['fases'][fase]
        avance = calcular_avance_fase(datos_fase)
        
        respuesta = {
            'nombre_fase': fase,
            'avance': avance
        }

        return jsonify(respuesta), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Endpoint para agregar un avance a una fase específica
@proyecto_bp.route('/<proyecto_id>/fase/<fase>/avance', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Agregar avance a una fase de un proyecto',
    'description': 'Este endpoint permite agregar un avance a una fase específica de un proyecto. Se requiere una descripción del avance y opcionalmente una fecha.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto al cual se le agregará el avance en la fase especificada'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase en la cual se agregará el avance'
        },
        {
            'name': 'descripcion',
            'in': 'body',
            'required': True,
            'type': 'string',
            'description': 'Descripción del avance realizado en la fase'
        },
        {
            'name': 'fecha',
            'in': 'body',
            'required': False,
            'type': 'string',
            'format': 'date',
            'description': 'Fecha del avance en formato YYYY-MM-DD. Si no se proporciona, se asignará la fecha actual.'
        }
    ],
    'responses': {
        200: {
            'description': 'Avance agregado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'},
                    'avance': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'description': 'ID único del avance'},
                            'descripcion': {'type': 'string', 'description': 'Descripción del avance'},
                            'fecha': {'type': 'string', 'description': 'Fecha del avance'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        400: {
            'description': 'Fase no válida o falta de descripción',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Error al agregar el avance',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Descripción del error'},
                    'tipo': {'type': 'string', 'description': 'Tipo de error'}
                }
            }
        }
    }
})
def agregar_avance_fase(proyecto_id, fase):
    try:
        datos = request.get_json()
        if not datos or 'descripcion' not in datos:
            return jsonify({'error': 'Se requiere una descripción del avance'}), 400

        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()
        
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        if 'fases' not in proyecto_data or fase not in proyecto_data['fases']:
            return jsonify({'error': 'Fase no válida'}), 400

        nuevo_avance = {
            'id': str(datetime.now().timestamp()),
            'descripcion': datos['descripcion'],
            'fecha': datos.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        }

        # Actualizar el documento
        if 'avances' in proyecto_data['fases'][fase]:
            proyecto_ref.update({
                f'fases.{fase}.avances': firestore.ArrayUnion([nuevo_avance])
            })
        else:
            proyecto_ref.update({
                f'fases.{fase}.avances': [nuevo_avance]
            })

        return jsonify({
            'mensaje': 'Avance agregado exitosamente',
            'avance': nuevo_avance
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Error al agregar el avance: {str(e)}',
            'tipo': type(e).__name__
        }), 500




docente_bp = Blueprint('docente', __name__)
db = firestore.client()

@docente_bp.route('/docente/proyecto/<proyecto_id>/fase/<fase>/comentar', methods=['POST'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Agregar comentario a una fase de un proyecto',
    'description': 'Este endpoint permite agregar un comentario (retroalimentación) a una fase de un proyecto. El comentario debe ser proporcionado por un docente.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto al cual se le agregará el comentario en la fase especificada'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase en la cual se agregará el comentario'
        },
        {
            'name': 'comentario',
            'in': 'body',
            'required': True,
            'type': 'string',
            'description': 'Comentario del docente que retroalimenta la fase'
        },
        {
            'name': 'docente_id',
            'in': 'body',
            'required': True,
            'type': 'string',
            'description': 'ID del docente que está agregando el comentario'
        }
    ],
    'responses': {
        200: {
            'description': 'Comentario agregado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'},
                    'comentario': {
                        'type': 'object',
                        'properties': {
                            'texto': {'type': 'string', 'description': 'Texto del comentario'},
                            'docente_id': {'type': 'string', 'description': 'ID del docente'},
                            'fecha': {'type': 'string', 'description': 'Fecha en que se realizó el comentario'},
                            'tipo': {'type': 'string', 'description': 'Tipo de comentario (retroalimentación)'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        400: {
            'description': 'El comentario está vacío o faltan parámetros',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        500: {
            'description': 'Error al agregar el comentario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Descripción del error'}
                }
            }
        }
    }
})
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

@proyecto_bp.route('/<proyecto_id>/comentarios', methods=['GET'])
def obtener_comentarios(proyecto_id):
    try:
        # Obtener el documento del proyecto
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get()

        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        comentarios = proyecto_data.get('comentarios', [])

        # Obtener información de los autores
        for comentario in comentarios:
            if 'autor_id' in comentario:
                autor = USUARIOS.document(comentario['autor_id']).get()
                if autor.exists:
                    autor_data = autor.to_dict()
                    comentario['autor_nombre'] = autor_data.get('nombre')
                    comentario['autor_rol'] = autor_data.get('rol')

        # Ordenar comentarios por fecha (más recientes primero)
        comentarios.sort(key=lambda x: x.get('fecha', ''), reverse=True)

        return jsonify(comentarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Agregar un comentario
@proyecto_bp.route('/<proyecto_id>/comentario', methods=['POST'])
def agregar_comentario(proyecto_id):
    try:
        datos = request.get_json()
        
        if not datos.get('texto'):
            return jsonify({'error': 'El comentario no puede estar vacío'}), 400

        nuevo_comentario = {
            'id': str(datetime.now().timestamp()),
            'texto': datos.get('texto'),
            'autor_id': datos.get('autor_id'),
            'fecha': datetime.now().isoformat(),
            'tipo': 'comentario'
        }

        # Obtener información del autor
        autor = USUARIOS.document(datos.get('autor_id')).get()
        print(autor.to_dict())
        if autor.exists:
            autor_data = autor.to_dict()
            nuevo_comentario['autor_nombre'] = autor_data.get('nombre')
            nuevo_comentario['autor_rol'] = autor_data.get('rol')
            nuevo_comentario['autor'] = autor_data
            print(nuevo_comentario)


        # Actualizar el proyecto con el nuevo comentario
        PROYECTOS.document(proyecto_id).update({
            'comentarios': firestore.ArrayUnion([nuevo_comentario])
        })
        
        return jsonify({
            'mensaje': 'Comentario agregado exitosamente',
            'comentario': nuevo_comentario
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Eliminar un comentario
@proyecto_bp.route('/<proyecto_id>/comentario/<comentario_id>', methods=['DELETE'])
def eliminar_comentario(proyecto_id, comentario_id):
    try:
        # Verificar que el usuario que elimina es el autor o tiene permisos
        usuario_id = request.args.get('usuario_id')
        
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        comentarios = proyecto_data.get('comentarios', [])
        
        # Encontrar y eliminar el comentario
        comentario_a_eliminar = None
        nuevos_comentarios = []
        
        for comentario in comentarios:
            if comentario.get('id') == comentario_id:
                # Verificar permisos
                if comentario.get('autor_id') != usuario_id:
                    return jsonify({'error': 'No tienes permiso para eliminar este comentario'}), 403
                comentario_a_eliminar = comentario
            else:
                nuevos_comentarios.append(comentario)

        if not comentario_a_eliminar:
            return jsonify({'error': 'Comentario no encontrado'}), 404

        # Actualizar el proyecto con la lista de comentarios actualizada
        PROYECTOS.document(proyecto_id).update({
            'comentarios': nuevos_comentarios
        })

        return jsonify({'mensaje': 'Comentario eliminado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Editar un comentario
@proyecto_bp.route('/<proyecto_id>/comentario/<comentario_id>', methods=['PUT'])
def editar_comentario(proyecto_id, comentario_id):
    try:
        datos = request.get_json()
        usuario_id = datos.get('usuario_id')
        nuevo_texto = datos.get('texto')

        if not nuevo_texto:
            return jsonify({'error': 'El comentario no puede estar vacío'}), 400

        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404

        proyecto_data = proyecto.to_dict()
        comentarios = proyecto_data.get('comentarios', [])
        
        # Encontrar y actualizar el comentario
        for comentario in comentarios:
            if comentario.get('id') == comentario_id:
                # Verificar permisos
                if comentario.get('autor_id') != usuario_id:
                    return jsonify({'error': 'No tienes permiso para editar este comentario'}), 403
                
                comentario['texto'] = nuevo_texto
                comentario['editado'] = True
                comentario['fecha_edicion'] = datetime.now().isoformat()
                break

        # Actualizar el proyecto con los comentarios modificados
        PROYECTOS.document(proyecto_id).update({
            'comentarios': comentarios
        })

        return jsonify({
            'mensaje': 'Comentario actualizado exitosamente',
            'comentario': comentario
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
# Obtener comentarios de una fase específica
@docente_bp.route('/docente/proyecto/<proyecto_id>/fase/<fase>/comentarios', methods=['GET'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Obtener comentarios de una fase de un proyecto',
    'description': 'Este endpoint permite obtener todos los comentarios (retroalimentación) de una fase específica de un proyecto.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto del cual se desean obtener los comentarios de la fase especificada'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase de la cual se desean obtener los comentarios'
        }
    ],
    'responses': {
        200: {
            'description': 'Comentarios obtenidos exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'comentarios': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'texto': {'type': 'string', 'description': 'Texto del comentario'},
                                'docente_id': {'type': 'string', 'description': 'ID del docente que hizo el comentario'},
                                'fecha': {'type': 'string', 'description': 'Fecha del comentario'},
                                'tipo': {'type': 'string', 'description': 'Tipo de comentario (retroalimentación)'}
                            }
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Proyecto no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        500: {
            'description': 'Error al obtener los comentarios',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Descripción del error'}
                }
            }
        }
    }
})
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

# Editar un comentario existente
@docente_bp.route('/docente/proyecto/<proyecto_id>/fase/<fase>/comentario/<int:comentario_index>', methods=['PUT'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Editar un comentario en una fase de un proyecto',
    'description': 'Este endpoint permite editar un comentario específico dentro de una fase de un proyecto. Solo el docente que hizo el comentario puede editarlo.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto donde se desea editar un comentario en la fase especificada.'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase donde se encuentra el comentario que se desea editar.'
        },
        {
            'name': 'comentario_index',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Índice del comentario en la lista de comentarios de la fase.'
        }
    ],
    'requestBody': {
        'description': 'Cuerpo del request para editar el comentario',
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'comentario': {'type': 'string', 'description': 'Nuevo texto del comentario'},
                        'docente_id': {'type': 'string', 'description': 'ID del docente que está editando el comentario'}
                    },
                    'required': ['comentario', 'docente_id']
                }
            }
        }
    },
    'responses': {
        200: {
            'description': 'Comentario actualizado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'},
                    'comentario': {
                        'type': 'object',
                        'properties': {
                            'texto': {'type': 'string', 'description': 'Texto del comentario actualizado'},
                            'docente_id': {'type': 'string', 'description': 'ID del docente que hizo el comentario'},
                            'fecha_edicion': {'type': 'string', 'description': 'Fecha en que se editó el comentario'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'El comentario no puede estar vacío o falta algún dato',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        403: {
            'description': 'El docente no tiene permiso para editar este comentario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        404: {
            'description': 'Proyecto o comentario no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        500: {
            'description': 'Error al editar el comentario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Descripción del error'}
                }
            }
        }
    }
})
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

# Eliminar un comentario
@docente_bp.route('/docente/proyecto/<proyecto_id>/fase/<fase>/comentario/<int:comentario_index>', methods=['DELETE'])
@swag_from({
    'tags': ['Proyectos'],
    'summary': 'Eliminar un comentario en una fase de un proyecto',
    'description': 'Este endpoint permite eliminar un comentario específico dentro de una fase de un proyecto. Solo el docente que hizo el comentario puede eliminarlo.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID del proyecto donde se desea eliminar un comentario en la fase especificada.'
        },
        {
            'name': 'fase',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Nombre de la fase donde se encuentra el comentario que se desea eliminar.'
        },
        {
            'name': 'comentario_index',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'Índice del comentario en la lista de comentarios de la fase.'
        },
        {
            'name': 'docente_id',
            'in': 'query',
            'required': True,
            'type': 'string',
            'description': 'ID del docente que está eliminando el comentario.'
        }
    ],
    'responses': {
        200: {
            'description': 'Comentario eliminado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'}
                }
            }
        },
        403: {
            'description': 'El docente no tiene permiso para eliminar este comentario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        404: {
            'description': 'Proyecto o comentario no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        500: {
            'description': 'Error al eliminar el comentario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Descripción del error'}
                }
            }
        }
    }
})
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
        
# Añadir estas importaciones al inicio de tu servicio_proyecto.py
from werkzeug.utils import secure_filename
from utils.storage_utils import (
    subir_archivo_supabase, 
    eliminar_archivo_supabase, 
    listar_archivos_proyecto
)

# Ejemplo de endpoint para subir archivo de proyecto
@proyecto_bp.route('/<proyecto_id>/archivo', methods=['POST'])
@swag_from({
    'tags': ['Archivos'],
    'summary': 'Subir archivo a un proyecto',
    'description': 'Endpoint para subir un archivo a un proyecto específico utilizando Supabase Storage.',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID del proyecto al que se subirá el archivo'
        },
        {
            'name': 'archivo',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Archivo a subir'
        },
        {
            'name': 'usuario_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'ID del usuario que sube el archivo'
        }
    ],
    'responses': {
        200: {
            'description': 'Archivo subido exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'},
                    'archivo': {
                        'type': 'object',
                        'properties': {
                            'nombre_original': {'type': 'string'},
                            'nombre_storage': {'type': 'string'},
                            'ruta_storage': {'type': 'string'},
                            'url': {'type': 'string'},
                            'tipo_mime': {'type': 'string'},
                            'tamano': {'type': 'integer'},
                            'fecha_subida': {'type': 'string', 'format': 'date-time'},
                            'subido_por': {'type': 'string'}
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Error al subir el archivo',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def subir_archivo_proyecto(proyecto_id):
    """
    Endpoint para subir un archivo a un proyecto
    """
    try:
        # Verificar que se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({'error': 'No se envió ningún archivo'}), 400
        
        archivo = request.files['archivo']
        
        # Validar que el archivo tenga un nombre
        if archivo.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        # Obtener usuario que sube el archivo (opcional)
        usuario_id = request.form.get('usuario_id')
        
        # Subir archivo a Supabase
        metadata_archivo = subir_archivo_supabase(
            archivo, 
            proyecto_id, 
            subcarpeta='documentos', 
            usuario_id=usuario_id
        )
        
        # Actualizar documento del proyecto en Firestore
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto_ref.update({
            'archivos': firestore.ArrayUnion([metadata_archivo])
        })
        
        return jsonify({
            'mensaje': 'Archivo subido exitosamente',
            'archivo': metadata_archivo
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error al subir archivo: {str(e)}'
        }), 400

# Endpoint para eliminar archivo de proyecto
@proyecto_bp.route('/<proyecto_id>/archivo/<nombre_archivo>', methods=['DELETE'])
@swag_from({
    'tags': ['Archivos'],
    'summary': 'Eliminar archivo de un proyecto',
    'description': 'Endpoint para eliminar un archivo específico de un proyecto utilizando Supabase Storage.',
    'parameters': [
        {
            'name': 'proyecto_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID del proyecto'
        },
        {
            'name': 'nombre_archivo',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Nombre del archivo en el storage'
        }
    ],
    'responses': {
        200: {
            'description': 'Archivo eliminado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Archivo no encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Error al eliminar el archivo',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def eliminar_archivo_proyecto(proyecto_id, nombre_archivo):
    """
    Endpoint para eliminar un archivo de un proyecto
    """
    try:
        # Obtener el proyecto
        proyecto_ref = PROYECTOS.document(proyecto_id)
        proyecto = proyecto_ref.get().to_dict()
        
        # Buscar el archivo en los metadatos del proyecto
        archivos = proyecto.get('archivos', [])
        archivo_a_eliminar = next(
            (archivo for archivo in archivos if archivo['nombre_storage'] == nombre_archivo), 
            None
        )
        
        if not archivo_a_eliminar:
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # Eliminar archivo de Supabase
        eliminado = eliminar_archivo_supabase(archivo_a_eliminar['ruta_storage'])
        
        if eliminado:
            # Eliminar referencia del archivo en Firestore
            proyecto_ref.update({
                'archivos': firestore.ArrayRemove([archivo_a_eliminar])
            })
            
            return jsonify({
                'mensaje': 'Archivo eliminado exitosamente'
            }), 200
        else:
            return jsonify({
                'error': 'No se pudo eliminar el archivo'
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': f'Error al eliminar archivo: {str(e)}'
        }), 400

# Endpoint para listar archivos de un proyecto
@proyecto_bp.route('/<proyecto_id>/archivos', methods=['GET'])
@swag_from({
    'tags': ['Archivos'],
    'summary': 'Listar archivos de un proyecto',
    'description': 'Endpoint para obtener la lista de archivos de un proyecto desde Supabase Storage y sus metadatos de Firestore.',
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
            'description': 'Lista de archivos obtenida exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'archivos_supabase': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'description': 'Metadatos del archivo según la respuesta de Supabase Storage'
                        }
                    },
                    'archivos_metadata': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'nombre_original': {'type': 'string'},
                                'nombre_storage': {'type': 'string'},
                                'ruta_storage': {'type': 'string'},
                                'url': {'type': 'string'},
                                'tipo_mime': {'type': 'string'},
                                'tamano': {'type': 'integer'},
                                'fecha_subida': {'type': 'string', 'format': 'date-time'},
                                'subido_por': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Error al listar archivos',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})

def listar_archivos_de_proyecto(proyecto_id):
    """
    Endpoint para listar todos los archivos de un proyecto
    """
    try:
        # Obtener archivos desde Supabase
        archivos_supabase = listar_archivos_proyecto(proyecto_id)
        
        # Obtener metadatos de archivos desde Firestore
        proyecto = PROYECTOS.document(proyecto_id).get().to_dict()
        archivos_metadata = proyecto.get('archivos', [])
        
        return jsonify({
            'archivos_supabase': archivos_supabase,
            'archivos_metadata': archivos_metadata
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error al listar archivos: {str(e)}'
        }), 400
        
@proyecto_bp.route('/crearsupa', methods=['POST'])
def crear_proyecto_supabase():
    try:
        datos = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'lider_id']
        for field in required_fields:
            if not datos.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400

        # Crear el proyecto en Supabase
        nuevo_proyecto = {
            'titulo': datos['titulo'],
            'descripcion': datos['descripcion'],
            'fecha_inicio': datos['fecha_inicio'],
            'fecha_fin': datos['fecha_fin'],
            'lider_id': datos['lider_id'],
            'docente_id': datos.get('docente_id'),
            'colaboradores_ids': datos.get('colaboradores', []),
            'facultad': datos.get('facultad'),
            'carrera': datos.get('carrera'),
            'estado': 'activo',
        }

        response = supabase.table('proyectos').insert(nuevo_proyecto).execute()
        
        if len(response.data) > 0:
            return jsonify({
                'mensaje': 'Proyecto creado exitosamente',
                'proyecto': response.data[0]
            }), 201
        else:
            return jsonify({'error': 'Error al crear el proyecto'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400
#BACKEND servicios\servicio_email.py
from flask import Blueprint, request, jsonify
from firebase_admin import auth, firestore
from configuracion.firebase_config import inicializar_firebase
from flasgger import swag_from

auth_bp = Blueprint('auth', __name__)
db = inicializar_firebase()
USUARIOS = db.collection('usuarios')

@auth_bp.route('/registro', methods=['POST'])
@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Registrar un nuevo usuario en el sistema',
    'description': 'Este endpoint permite registrar un nuevo usuario en el sistema, asignándole un rol y validando su información.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {
                        'type': 'string',
                        'description': 'Correo electrónico del nuevo usuario',
                        'example': 'usuario@ejemplo.com'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'Contraseña para el nuevo usuario',
                        'example': 'contrasena_segura'
                    },
                    'nombre': {
                        'type': 'string',
                        'description': 'Nombre del nuevo usuario',
                        'example': 'Juan Pérez'
                    },
                    'rol': {
                        'type': 'string',
                        'description': 'Rol asignado al usuario',
                        'enum': ['admin', 'director_programa', 'lider_proyecto', 'colaborador', 'docente_guia'],
                        'example': 'colaborador'
                    }
                },
                'required': ['email', 'password', 'nombre', 'rol']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Usuario registrado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'},
                    'uid': {'type': 'string', 'description': 'ID único del usuario'},
                    'aprobado': {'type': 'boolean', 'description': 'Estado de aprobación del usuario'}
                }
            }
        },
        400: {
            'description': 'Error de validación o parámetros inválidos',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        }
    }
})
def registro():
    try:
        datos = request.get_json()
        email = datos.get('email')
        password = datos.get('password')
        nombre = datos.get('nombre')
        rol = datos.get('rol')

        # Validar rol
        roles_permitidos = ['admin', 'director_programa', 'lider_proyecto', 'colaborador', 'docente_guia']
        if rol not in roles_permitidos:
            return jsonify({
                'error': 'Rol inválido. Los roles permitidos son: admin, director_programa, lider_proyecto, colaborador, docente_guia'
            }), 400

        usuario = auth.create_user(
            email=email,
            password=password,
            display_name=nombre
        )

        # Por defecto los usuarios están pendientes de aprobación, excepto admin
        aprobado = rol == 'admin'
        
        USUARIOS.document(usuario.uid).set({
            'uid': usuario.uid,
            'email': email,
            'nombre': nombre,
            'rol': rol,
            'aprobado': aprobado,
            'fecha_registro': firestore.SERVER_TIMESTAMP
        })

        mensaje = 'Usuario registrado exitosamente'
        if not aprobado:
            mensaje += '. Pendiente de aprobación por un administrador'

        return jsonify({
            'mensaje': mensaje,
            'uid': usuario.uid,
            'aprobado': aprobado
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Iniciar sesión de usuario',
    'description': 'Este endpoint permite que los usuarios inicien sesión proporcionando su correo electrónico y contraseña.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {
                        'type': 'string',
                        'description': 'Correo electrónico del usuario que intenta iniciar sesión',
                        'example': 'usuario@ejemplo.com'
                    },
                    'password': {
                        'type': 'string',
                        'description': 'Contraseña del usuario',
                        'example': 'contrasena_segura'
                    }
                },
                'required': ['email', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Inicio de sesión exitoso',
            'schema': {
                'type': 'object',
                'properties': {
                    'uid': {'type': 'string', 'description': 'ID único del usuario'},
                    'email': {'type': 'string', 'description': 'Correo electrónico del usuario'},
                    'nombre': {'type': 'string', 'description': 'Nombre del usuario'},
                    'rol': {'type': 'string', 'description': 'Rol del usuario'}
                }
            }
        },
        401: {
            'description': 'Credenciales inválidas',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        },
        403: {
            'description': 'Usuario pendiente de aprobación',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        }
    }
})
def login():
    try:
        datos = request.get_json()
        email = datos.get('email')
        password = datos.get('password')

        usuario = auth.get_user_by_email(email)
        usuario_data = USUARIOS.document(usuario.uid).get().to_dict()

        # Verificar si el usuario está aprobado
        if not usuario_data.get('aprobado', False) and usuario_data.get('rol') != 'admin':
            return jsonify({'error': 'Usuario pendiente de aprobación'}), 403

        return jsonify({
            'uid': usuario.uid,
            'email': email,
            'nombre': usuario_data.get('nombre'),
            'rol': usuario_data.get('rol')
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Credenciales inválidas'}), 401

@auth_bp.route('/admin/usuarios-pendientes', methods=['GET'])
@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Obtener usuarios pendientes de aprobación',
    'description': 'Este endpoint permite obtener una lista de usuarios que aún no han sido aprobados, es decir, aquellos que tienen el campo "aprobado" en False.',
    'responses': {
        200: {
            'description': 'Lista de usuarios pendientes de aprobación',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'uid': {'type': 'string', 'description': 'ID único del usuario'},
                        'nombre': {'type': 'string', 'description': 'Nombre del usuario'},
                        'email': {'type': 'string', 'description': 'Correo electrónico del usuario'},
                        'rol': {'type': 'string', 'description': 'Rol del usuario'}
                    }
                }
            }
        },
        400: {
            'description': 'Error al obtener los usuarios pendientes',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        }
    }
})
def obtener_usuarios_pendientes():
    try:
        usuarios = USUARIOS.where('aprobado', '==', False).get()
        usuarios_data = [{
            'uid': user.id,
            'nombre': user.get('nombre'),
            'email': user.get('email'),
            'rol': user.get('rol')
        } for user in usuarios]
        return jsonify(usuarios_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/admin/aprobar/<uid>', methods=['POST'])
@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Aprobar usuario pendiente',
    'description': 'Este endpoint permite aprobar a un usuario pendiente, cambiando su estado de "aprobado" a True.',
    'parameters': [
        {
            'name': 'uid',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'ID único del usuario a aprobar'
        }
    ],
    'responses': {
        200: {
            'description': 'Usuario aprobado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensaje': {'type': 'string', 'description': 'Mensaje de éxito'}
                }
            }
        },
        400: {
            'description': 'Error al aprobar el usuario',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        }
    }
})
def aprobar_usuario(uid):
    try:
        USUARIOS.document(uid).update({
            'aprobado': True
        })
        return jsonify({'mensaje': 'Usuario aprobado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/admin/usuarios', methods=['GET'])
@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Listar todos los usuarios',
    'description': 'Este endpoint permite obtener la lista de todos los usuarios registrados en el sistema.',
    'responses': {
        200: {
            'description': 'Lista de usuarios obtenida exitosamente',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'uid': {'type': 'string', 'description': 'ID único del usuario'},
                        'nombre': {'type': 'string', 'description': 'Nombre del usuario'},
                        'email': {'type': 'string', 'description': 'Correo electrónico del usuario'},
                        'rol': {'type': 'string', 'description': 'Rol del usuario'},
                        'aprobado': {'type': 'boolean', 'description': 'Estado de aprobación del usuario'},
                        'fecha_registro': {'type': 'string', 'description': 'Fecha de registro del usuario'}
                    }
                }
            }
        },
        400: {
            'description': 'Error al obtener la lista de usuarios',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Mensaje de error'}
                }
            }
        }
    }
})
def listar_usuarios():
    try:
        usuarios = USUARIOS.get()
        usuarios_data = []
        for user in usuarios:
            data = user.to_dict()
            data['uid'] = user.id
            usuarios_data.append(data)
        return jsonify(usuarios_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
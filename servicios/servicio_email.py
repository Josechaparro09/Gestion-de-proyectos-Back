from flask import Blueprint, request, jsonify
from flasgger import swag_from
from supabase import create_client, Client
from datetime import datetime
import logging
from configuracion.supabase_configuration import supabase_client

# Inicializar cliente de Supabase
supabase: Client = supabase_client
auth_bp = Blueprint('auth', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@auth_bp.route('/registro', methods=['POST'])
@swag_from({
    'tags': ['Autenticación'],
    'summary': 'Registrar un nuevo usuario',
    'description': 'Crea un nuevo usuario en el sistema con el rol especificado',
    'parameters': [{
        'in': 'body',
        'name': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'example': 'usuario@ejemplo.com'},
                'password': {'type': 'string', 'example': 'contraseña123'},
                'nombre': {'type': 'string', 'example': 'Juan Pérez'},
                'rol': {'type': 'string', 'enum': [
                    'admin', 'director_programa', 'lider_proyecto', 
                    'colaborador', 'docente_guia'
                ]}
            }
        }
    }],
    'responses': {
        201: {'description': 'Usuario registrado exitosamente'},
        400: {'description': 'Error en los datos proporcionados'}
    }
})
def registro():
    try:
        data = request.get_json()
        required_fields = ['email', 'password', 'nombre', 'rol']
        
        # Validar campos requeridos
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400

        # Registrar usuario en Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })

        if not auth_response.user:
            return jsonify({'error': 'Error al crear el usuario'}), 400

        # Crear registro en la tabla usuarios
        user_data = {
            'id': auth_response.user.id,
            'email': data['email'],
            'nombre': data['nombre'],
            'rol': data['rol'],
            'aprobado': data['rol'] == 'admin',  # Solo admin se auto-aprueba
            'fecha_registro': datetime.utcnow().isoformat()
        }

        result = supabase.table('usuarios').insert(user_data).execute()

        if result.data:
            return jsonify({
                'mensaje': 'Usuario registrado exitosamente',
                'uid': auth_response.user.id,
                'aprobado': user_data['aprobado']
            }), 201
        else:
            # Rollback: eliminar usuario de auth si falla la inserción en la tabla
            supabase.auth.admin.delete_user(auth_response.user.id)
            return jsonify({'error': 'Error al guardar los datos del usuario'}), 400

    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Autenticación'],
    'summary': 'Iniciar sesión',
    'description': 'Autentica un usuario y devuelve su información',
    'parameters': [{
        'in': 'body',
        'name': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string'},
                'password': {'type': 'string'}
            }
        }
    }],
    'responses': {
        200: {'description': 'Login exitoso'},
        401: {'description': 'Credenciales inválidas'},
        403: {'description': 'Usuario no aprobado'}
    }
})
def login():
    try:
        data = request.get_json()
        
        # Autenticar con Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })

        if not auth_response.user:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        # Obtener información adicional del usuario
        user_query = supabase.table('usuarios')\
            .select('*')\
            .eq('id', auth_response.user.id)\
            .single()\
            .execute()

        if not user_query.data:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        user_data = user_query.data
        
        # Verificar si el usuario está aprobado
        if not user_data['aprobado'] and user_data['rol'] != 'admin':
            return jsonify({'error': 'Usuario pendiente de aprobación'}), 403

        return jsonify({
            'uid': user_data['id'],
            'email': user_data['email'],
            'nombre': user_data['nombre'],
            'rol': user_data['rol']
        }), 200

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error en la autenticación'}), 401

@auth_bp.route('/admin/usuarios', methods=['GET'])
@swag_from({
    'tags': ['Administración'],
    'summary': 'Obtener todos los usuarios',
    'description': 'Retorna la lista de todos los usuarios registrados',
    'responses': {
        200: {'description': 'Lista de usuarios obtenida exitosamente'},
        400: {'description': 'Error al obtener usuarios'}
    }
})
def listar_usuarios():
    try:
        response = supabase.table('usuarios').select('*').execute()
        return jsonify(response.data), 200
    except Exception as e:
        logger.error(f"Error al listar usuarios: {str(e)}")
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/admin/aprobar/<uid>', methods=['POST'])
@swag_from({
    'tags': ['Administración'],
    'summary': 'Aprobar usuario',
    'description': 'Aprueba un usuario pendiente',
    'parameters': [{
        'name': 'uid',
        'in': 'path',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {'description': 'Usuario aprobado exitosamente'},
        400: {'description': 'Error al aprobar usuario'},
        404: {'description': 'Usuario no encontrado'}
    }
})
def aprobar_usuario(uid):
    try:
        # Verificar si el usuario existe
        user_query = supabase.table('usuarios')\
            .select('*')\
            .eq('id', uid)\
            .single()\
            .execute()

        if not user_query.data:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Actualizar estado de aprobación
        response = supabase.table('usuarios')\
            .update({'aprobado': True})\
            .eq('id', uid)\
            .execute()

        if response.data:
            return jsonify({'mensaje': 'Usuario aprobado exitosamente'}), 200
        else:
            return jsonify({'error': 'Error al aprobar usuario'}), 400

    except Exception as e:
        logger.error(f"Error al aprobar usuario: {str(e)}")
        return jsonify({'error': str(e)}), 400
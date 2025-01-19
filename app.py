from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from configuracion.firebase_config import inicializar_firebase
from servicios.servicio_email import auth_bp
from servicios.servicio_programa import programa_bp
from servicios.servicio_proyecto import proyecto_bp
from servicios.servicio_colaborador import colaborador_bp
from servicios.servicio_docente import docente_bp
from servicios.servicio_director import director_bp
from servicios.servicio_tareas import task_bp
from configuracion.supabase_configuration import inicializar_supabase

app = Flask(__name__)

# Configuración de CORS
CORS(app, origins=["http://localhost:5173"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configuración de Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
    "title": "API de Gestión Académica",
    "description": "API para la gestión de programas, proyectos, docentes y directores",
    "version": "1.0.0"
}

swagger = Swagger(app, config=swagger_config)

# Inicializar servicios
db = inicializar_firebase()
supabase = inicializar_supabase()

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(programa_bp, url_prefix='/programa')
app.register_blueprint(proyecto_bp, url_prefix='/proyecto')
app.register_blueprint(colaborador_bp, url_prefix='/colaborador')
app.register_blueprint(docente_bp, url_prefix='/docente')
app.register_blueprint(director_bp, url_prefix='/director')
# app.register_blueprint(task_bp, url_prefix='/tareas')
app.register_blueprint(task_bp, url_prefix='/task')

@app.route('/test')
def test():
    """
    Endpoint de prueba
    ---
    responses:
      200:
        description: Servidor funcionando correctamente
        schema:
          properties:
            mensaje:
              type: string
              description: Mensaje de estado del servidor
    """
    return {'mensaje': 'Servidor funcionando correctamente'}

@app.errorhandler(404)
def not_found(error):
    """
    Manejador de errores 404
    """
    return {'error': 'Recurso no encontrado'}, 404

@app.errorhandler(500)
def internal_error(error):
    """
    Manejador de errores 500
    """
    return {'error': 'Error interno del servidor'}, 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
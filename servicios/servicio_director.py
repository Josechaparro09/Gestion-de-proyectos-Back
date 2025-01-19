#BACKEND servicios\servicio_director.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

director_bp = Blueprint('director', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

# Ruta para obtener estadísticas de proyectos (completados, en progreso, etc.)
@director_bp.route('/estadisticas/<director_id>', methods=['GET'])
def obtener_estadisticas(director_id):
    try:
        print(f"Obteniendo estadísticas para director_id: {director_id}")  # Log
        proyectos = PROYECTOS.where('lider_id', '==', director_id).get()

        total_proyectos = len(proyectos)
        completados = 0
        en_progreso = 0

        for proyecto in proyectos:
            estado = proyecto.get('estado')
            if estado == 'completado':
                completados += 1
            elif estado == 'activo':
                en_progreso += 1

        estadisticas = {
            'total_proyectos': total_proyectos,
            'completados': completados,
            'en_progreso': en_progreso,
            'porcentaje_completados': (completados / total_proyectos) * 100 if total_proyectos > 0 else 0,
            'porcentaje_en_progreso': (en_progreso / total_proyectos) * 100 if total_proyectos > 0 else 0,
        }

        return jsonify(estadisticas)
    except Exception as e:
        print(f"Error: {e}")  # Log del error
        return jsonify({'error': str(e)}), 400

# Ruta para agregar comentarios a los proyectos
@director_bp.route('/proyecto/<proyecto_id>/comentar', methods=['POST'])
def comentar_proyecto(proyecto_id):
    try:
        datos = request.get_json()
        comentario = {
            'texto': datos.get('texto'),
            'director_id': datos.get('director_id'),
            'fecha': str(datetime.now())
        }

        PROYECTOS.document(proyecto_id).update({
            'comentarios_director': firestore.ArrayUnion([comentario])
        })
        return jsonify({'mensaje': 'Comentario agregado exitosamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Ruta para obtener detalles de un director
@director_bp.route('/director/<id>', methods=['GET'])
def obtener_director(id):
    try:
        director_ref = db.collection('usuarios').document(id)
        director = director_ref.get()

        if director.exists:
            return jsonify(director.to_dict())
        else:
            return jsonify({'error': 'Director no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@director_bp.route('/mis-proyectos/<director_id>', methods=['GET'])
def obtener_proyectos(director_id):
    # Esta ruta obtiene los proyectos asignados al director.
    try:
        proyectos = PROYECTOS.where('lider_id', '==', director_id).get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@director_bp.route('/proyectos/<proyecto_id>', methods=['GET'])
def obtener_proyecto_por_id(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if proyecto.exists:
            return jsonify({
                'id': proyecto.id,
                **proyecto.to_dict()
            })
        else:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@director_bp.route('/proyectos', methods=['GET'])
def obtener_todos_los_proyectos():
    try:
        # Obtener todos los proyectos de la colección sin filtros
        proyectos = PROYECTOS.get()
        return jsonify([{
            'id': p.id,
            **p.to_dict()
        } for p in proyectos])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Script de prueba
def test_director():
    BASE_URL = 'http://localhost:5000/director'
    DIRECTOR_ID = {"uid"}  # ID del director

    # Ver proyectos asignados
    response = requests.get(f'{BASE_URL}/mis-proyectos/{DIRECTOR_ID}')
    print('Proyectos asignados:', response.json())

    # Ver estadísticas
    response = requests.get(f'{BASE_URL}/estadisticas/{DIRECTOR_ID}')
    print('Estadísticas:', response.json())

    if response.json():
        proyecto = response.json()[0]
        proyecto_id = proyecto['id']
        
        # Comentar proyecto
        comentario = {
            "texto": "Excelente progreso en este proyecto",
            "director_id": DIRECTOR_ID
        }
        response = requests.post(f'{BASE_URL}/proyecto/{proyecto_id}/comentar', json=comentario)
        print('\nComentar proyecto:', response.json())

if __name__ == '__main__':
    import requests
    test_director()

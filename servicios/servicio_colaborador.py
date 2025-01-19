# BACKEND servicios/servicio_colaborador.py
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
from configuracion.firebase_config import inicializar_firebase

colaborador_bp = Blueprint('colaborador', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

@colaborador_bp.route('/mis-proyectos/<colaborador_id>', methods=['GET'])
def obtener_proyectos(colaborador_id):
   try:
       proyectos = PROYECTOS.where('colaboradores', 'array_contains', colaborador_id).get()
       
       proyectos_info = []
       for proyecto in proyectos:
           data = proyecto.to_dict()
           tareas_colaborador = [t for t in data.get('tareas', []) 
                               if t.get('asignado_a') == colaborador_id]
           
           # Calcular porcentaje de avance
           total_tareas = len(tareas_colaborador)
           tareas_completadas = len([t for t in tareas_colaborador 
                                   if t.get('estado') == 'completada'])
           
           porcentaje = (tareas_completadas / total_tareas * 100) if total_tareas > 0 else 0
           
           proyectos_info.append({
               'id': proyecto.id,
               'titulo': data.get('titulo'),
               'descripcion': data.get('descripcion'),
               'fecha_inicio': data.get('fecha_inicio'),
               'fecha_fin': data.get('fecha_fin'),
               'tareas_asignadas': tareas_colaborador,
               'porcentaje_avance': round(porcentaje, 2)
           })
           
       return jsonify(proyectos_info)
   except Exception as e:
       return jsonify({'error': str(e)}), 400

@colaborador_bp.route('/completar-tarea/<proyecto_id>', methods=['POST'])
def completar_tarea(proyecto_id):
   try:
       datos = request.get_json()
       colaborador_id = datos.get('colaborador_id')
       tarea_titulo = datos.get('tarea_titulo')
       
       proyecto_ref = PROYECTOS.document(proyecto_id)
       proyecto = proyecto_ref.get().to_dict()
       
       tareas_actualizadas = []
       for tarea in proyecto.get('tareas', []):
           if (tarea.get('titulo') == tarea_titulo and 
               tarea.get('asignado_a') == colaborador_id):
               tarea['estado'] = 'completada'
               tarea['fecha_completado'] = str(datetime.now())
           tareas_actualizadas.append(tarea)
       
       proyecto_ref.update({
           'tareas': tareas_actualizadas
       })
       
       return jsonify({'mensaje': 'Tarea completada exitosamente'})
   except Exception as e:
       return jsonify({'error': str(e)}), 400
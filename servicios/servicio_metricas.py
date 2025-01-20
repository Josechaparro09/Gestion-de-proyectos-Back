#BACKEND servicios\servicio_metricas.py
from flask import Blueprint, jsonify
from firebase_admin import firestore
from datetime import datetime, timedelta
from configuracion.firebase_config import inicializar_firebase

metrics_bp = Blueprint('metrics', __name__)
db = inicializar_firebase()
PROYECTOS = db.collection('proyectos')

@metrics_bp.route('/dashboard/<facultad>', methods=['GET'])
def obtener_metricas_facultad(facultad):
    try:
        proyectos = PROYECTOS.where('facultad', '==', facultad).get()
        
        metricas = {
            'total_proyectos': 0,
            'proyectos_activos': 0,
            'proyectos_completados': 0,
            'tiempo_promedio_fase': 0,
            'distribucion_estados': {},
            'progreso_promedio': 0,
            'proyectos_retrasados': 0
        }
        
        tiempo_total_fases = timedelta()
        total_fases_completadas = 0
        
        for proyecto in proyectos:
            data = proyecto.to_dict()
            metricas['total_proyectos'] += 1
            
            # Contar estados
            estado = data.get('estado', 'sin_estado')
            metricas['distribucion_estados'][estado] = metricas['distribucion_estados'].get(estado, 0) + 1
            
            if estado == 'activo':
                metricas['proyectos_activos'] += 1
            elif estado == 'completado':
                metricas['proyectos_completados'] += 1
                
            # Calcular tiempos de fase
            for fase, datos_fase in data.get('fases', {}).items():
                if datos_fase.get('completada'):
                    total_fases_completadas += 1
                    fecha_inicio = datetime.fromisoformat(datos_fase.get('fecha_inicio', ''))
                    fecha_fin = datetime.fromisoformat(datos_fase.get('fecha_fin', ''))
                    tiempo_total_fases += (fecha_fin - fecha_inicio)
            
            # Verificar retrasos
            fecha_fin = datetime.fromisoformat(data.get('fecha_fin', ''))
            if fecha_fin < datetime.now() and estado != 'completado':
                metricas['proyectos_retrasados'] += 1
                
        # Calcular promedios
        if total_fases_completadas > 0:
            tiempo_promedio = tiempo_total_fases / total_fases_completadas
            metricas['tiempo_promedio_fase'] = tiempo_promedio.days
            
        if metricas['total_proyectos'] > 0:
            metricas['progreso_promedio'] = (metricas['proyectos_completados'] / metricas['total_proyectos']) * 100
            
        return jsonify(metricas)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@metrics_bp.route('/proyecto/<proyecto_id>/metricas', methods=['GET'])
def obtener_metricas_proyecto(proyecto_id):
    try:
        proyecto = PROYECTOS.document(proyecto_id).get()
        if not proyecto.exists:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
            
        data = proyecto.to_dict()
        fecha_inicio = datetime.fromisoformat(data.get('fecha_inicio', ''))
        fecha_actual = datetime.now()
        
        metricas = {
            'dias_transcurridos': (fecha_actual - fecha_inicio).days,
            'fases_completadas': sum(1 for fase in data.get('fases', {}).values() if fase.get('completada')),
            'total_fases': len(data.get('fases', {})),
            'total_tareas': len(data.get('tareas', [])),
            'tareas_completadas': sum(1 for tarea in data.get('tareas', []) if tarea.get('estado') == 'completada'),
            'comentarios_docente': len(data.get('comentarios_docente', [])),
            'ultima_actividad': max(
                [data.get('fecha_creacion')] + 
                [tarea.get('fecha_completado') for tarea in data.get('tareas', []) if tarea.get('fecha_completado')]
            )
        }
        
        # Calcular porcentajes
        if metricas['total_tareas'] > 0:
            metricas['porcentaje_tareas_completadas'] = (metricas['tareas_completadas'] / metricas['total_tareas']) * 100
            
        if metricas['total_fases'] > 0:
            metricas['porcentaje_fases_completadas'] = (metricas['fases_completadas'] / metricas['total_fases']) * 100
            
        return jsonify(metricas)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@metrics_bp.route('/facultades/comparativa', methods=['GET'])
def comparativa_facultades():
    try:
        facultades = {}
        proyectos = PROYECTOS.get()
        
        for proyecto in proyectos:
            data = proyecto.to_dict()
            facultad = data.get('facultad')
            
            if facultad not in facultades:
                facultades[facultad] = {
                    'total_proyectos': 0,
                    'completados': 0,
                    'en_progreso': 0,
                    'retrasados': 0
                }
                
            facultades[facultad]['total_proyectos'] += 1
            
            if data.get('estado') == 'completado':
                facultades[facultad]['completados'] += 1
            elif data.get('estado') == 'activo':
                facultades[facultad]['en_progreso'] += 1
                
            fecha_fin = datetime.fromisoformat(data.get('fecha_fin', ''))
            if fecha_fin < datetime.now() and data.get('estado') != 'completado':
                facultades[facultad]['retrasados'] += 1
                
        # Calcular porcentajes para cada facultad
        for facultad in facultades:
            total = facultades[facultad]['total_proyectos']
            if total > 0:
                facultades[facultad]['porcentaje_completados'] = (facultades[facultad]['completados'] / total) * 100
                facultades[facultad]['porcentaje_retrasados'] = (facultades[facultad]['retrasados'] / total) * 100
                
        return jsonify(facultades)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
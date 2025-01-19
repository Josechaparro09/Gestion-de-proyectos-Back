import requests

BASE_URL = 'http://localhost:5000/docente'
DOCENTE_ID = "V1mfUZxuFcOHRAr7oDRN8OPDHTr2"  # ID del docente

def test_docente():
    # Ver proyectos asignados
    response = requests.get(f'{BASE_URL}/mis-proyectos/{DOCENTE_ID}')
    print('Proyectos asignados:', response.json())

    if response.json():
        proyecto = response.json()[0]  # Tomamos el primer proyecto
        proyecto_id = proyecto['id']
        
        # Comentar en el proyecto
        comentario_proyecto = {
            "texto": "El proyecto muestra buen progreso. Sugiero enfocarse en la documentación.",
            "docente_id": DOCENTE_ID
        }
        response = requests.post(f'{BASE_URL}/{proyecto_id}/comentar', json=comentario_proyecto)
        print('\nComentario en proyecto:', response.json())
        
        # Ver tareas del proyecto
        tareas = proyecto.get('tareas', [])
        print('\nTareas del proyecto:', tareas)
        
        # Comentar en una tarea específica si existe y tiene ID
        if tareas and 'id' in tareas[0]:
            tarea = tareas[0]
            comentario_tarea = {
                "texto": "Buen trabajo. Considerar agregar más pruebas unitarias.",
                "docente_id": DOCENTE_ID
            }
            response = requests.post(
                f'{BASE_URL}/{proyecto_id}/tarea/{tarea["id"]}/comentar', 
                json=comentario_tarea
            )
            print('\nComentario en tarea:', response.json())
        else:
            print('\nNo hay tareas con ID para comentar')
        
        # Ver avance actualizado
        response = requests.get(f'{BASE_URL}/mis-proyectos/{DOCENTE_ID}')
        print('\nAvance actualizado del proyecto:', response.json())

if __name__ == '__main__':
    test_docente()
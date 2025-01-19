# test_colaborador.py
import requests

BASE_URL = 'http://localhost:5000/colaborador'
COLABORADOR_ID = "HxcqK2CwMVM1OBX6BcuqRfqdmsB3"  # ID del colaborador

def test_colaborador():
    # Ver proyectos asignados
    response = requests.get(f'{BASE_URL}/mis-proyectos/{COLABORADOR_ID}')
    print('Proyectos asignados:', response.json())
    
    if response.json():
        proyecto = response.json()[0]
        # Completar una tarea
        if proyecto.get('tareas_asignadas'):
            tarea = proyecto['tareas_asignadas'][0]
            datos = {
                "colaborador_id": COLABORADOR_ID,
                "tarea_titulo": tarea['titulo']
            }
            response = requests.post(f'{BASE_URL}/completar-tarea/{proyecto["id"]}', json=datos)
            print('\nCompletar tarea:', response.json())
            
            # Ver avance actualizado
            response = requests.get(f'{BASE_URL}/mis-proyectos/{COLABORADOR_ID}')
            print('\nAvance actualizado:', response.json())

if __name__ == '__main__':
    test_colaborador()
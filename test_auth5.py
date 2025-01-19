# test_lider.py
import requests

BASE_URL = 'http://localhost:5000/proyecto'
LIDER_ID = "qX5GedcPZ0VrNK8l93C5o5Z5Hml1"  # ID del líder aprobado

def test_lider_proyecto():
    # Crear proyecto
    proyecto = {
        "titulo": "Proyecto Lider Test",
        "descripcion": "Proyecto de prueba del líder",
        "fecha_inicio": "2024-01-01",
        "fecha_fin": "2024-12-31",
        "lider_id": LIDER_ID
    }
    response = requests.post(f'{BASE_URL}/crear', json=proyecto)
    print('Creación proyecto:', response.json())
    proyecto_id = response.json().get('id')

    if proyecto_id:
        # Crear tarea
        tarea = {
            "titulo": "Tarea Test",
            "descripcion": "Tarea de prueba",
            "asignado_a": LIDER_ID,
            "fecha_inicio": "2024-01-15",
            "fecha_fin": "2024-02-15"
        }
        response = requests.post(f'{BASE_URL}/{proyecto_id}/tarea', json=tarea)
        print('\nCreación tarea:', response.json())

        # Asignar docente
        response = requests.post(f'{BASE_URL}/{proyecto_id}/docente', json={
            "docente_id": "V1mfUZxuFcOHRAr7oDRN8OPDHTr2"  # ID de un docente
        })
        print('\nAsignación docente:', response.json())

        # Asignar colaborador
        response = requests.post(f'{BASE_URL}/{proyecto_id}/colaborador', json={
            "colaborador_id": "HxcqK2CwMVM1OBX6BcuqRfqdmsB3"  # ID de un colaborador
        })
        print('\nAsignación colaborador:', response.json())

        # Ver avance
        response = requests.get(f'{BASE_URL}/{proyecto_id}/avance')
        print('\nAvance del proyecto:', response.json())

if __name__ == '__main__':
    test_lider_proyecto()
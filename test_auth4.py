# test_programa.py
import requests

BASE_URL = 'http://localhost:5000/programa'
DIRECTOR_ID = "ZxIqL714dKgwXPaavHQD9emGxHd2"

def test_director_programa():
    # Login como director
    auth_data = {
        "email": "test_director_programa@ejemplo.com",
        "password": "123456"
    }
    
    # Login
    response = requests.post('http://localhost:5000/auth/login', json=auth_data)
    print('Login director:', response.json())

    # Crear proyecto
    proyecto = {
        "titulo": "Proyecto Test",
        "descripcion": "Proyecto para pruebas",
        "fase": "planificacion",
        "estado": "activo",
        "fecha_inicio": "2024-01-01",
        "fecha_fin": "2024-12-31",
        "director_id": DIRECTOR_ID
    }
    response = requests.post(f'{BASE_URL}/proyectos', json=proyecto)
    print('\nCreación proyecto:', response.json())
    proyecto_id = response.json().get('id')

    # Ver lista de proyectos
    response = requests.get(f'{BASE_URL}/proyectos')
    print('\nLista de proyectos:', response.json())

    if proyecto_id:
        # Ver progreso
        response = requests.get(f'{BASE_URL}/proyectos/{proyecto_id}/progreso')
        print('\nProgreso del proyecto:', response.json())

        # Agregar comentario
        comentario = {
            "texto": "Revisión completada",
            "autor_id": DIRECTOR_ID
        }
        response = requests.post(f'{BASE_URL}/proyectos/{proyecto_id}/comentario', json=comentario)
        print('\nAgregar comentario:', response.json())

    # Estadísticas
    response = requests.get(f'{BASE_URL}/estadisticas')
    print('\nEstadísticas:', response.json())

if __name__ == '__main__':
    test_director_programa()
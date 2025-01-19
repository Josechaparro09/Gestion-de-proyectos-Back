# test_auth.py
import requests

BASE_URL = 'http://localhost:5000/auth'

def test_registro_roles():
   roles = ['admin', 'director_programa', 'lider_proyecto', 'colaborador', 'docente_guia']
   
   for rol in roles:
       data = {
           "email": f"test_{rol}@ejemplo.com",
           "password": "123456",
           "nombre": f"Usuario {rol.title()}",
           "rol": rol
       }
       print(f"\nRegistrando usuario {rol}...")
       response = requests.post(f'{BASE_URL}/registro', json=data)
       print(f"Respuesta: {response.json()}")
       
       print(f"Intentando login con {rol}...")
       login_data = {
           "email": f"test_{rol}@ejemplo.com",
           "password": "123456"
       }
       response = requests.post(f'{BASE_URL}/login', json=login_data)
       print(f"Respuesta login: {response.json()}")

if __name__ == '__main__':
   test_registro_roles()
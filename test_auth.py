import requests

BASE_URL = 'http://localhost:5000/auth'

def test_registro():
    data = {
        "email": "josemk@gmail.com",
        "password": "123456",
        "nombre": "Usuario Prueba"
    }
    response = requests.post(f'{BASE_URL}/registro', json=data)
    print('Respuesta registro:', response.json())

def test_login():
    data = {
        "email": "josemk@gmail.com",
        "password": "123456"
    }
    response = requests.post(f'{BASE_URL}/login', json=data)
    print('Respuesta login:', response.json())

if __name__ == '__main__':
    test_registro()
    test_login()
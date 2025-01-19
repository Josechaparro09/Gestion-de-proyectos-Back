import requests

BASE_URL = 'http://localhost:5000/auth'

def test_registro_nuevos_usuarios():
    usuarios = [
        {
            "email": "admin2@ejemplo.com",
            "password": "123456",
            "nombre": "Admin Nuevo",
            "rol": "admin"
        },
        {
            "email": "director2@ejemplo.com",
            "password": "123456",
            "nombre": "Director Nuevo",
            "rol": "director_programa"
        }
    ]
    
    for usuario in usuarios:
        response = requests.post(f'{BASE_URL}/registro', json=usuario)
        print(f'Registro {usuario["rol"]}:', response.json())
        if usuario["rol"] == "admin":
            return usuario["email"]  # Retornamos el email del admin para login

def test_admin_functions(admin_email):
    # Login como admin
    login_data = {
        "email": admin_email,
        "password": "123456"
    }
    login = requests.post(f'{BASE_URL}/login', json=login_data)
    print('Login admin:', login.json())

    # Obtener usuarios pendientes
    pendientes = requests.get(f'{BASE_URL}/admin/usuarios-pendientes')
    print('\nUsuarios pendientes:', pendientes.json())

    # Aprobar usuarios
    for usuario in pendientes.json():
        aprobar = requests.post(f'{BASE_URL}/admin/aprobar/{usuario["uid"]}')
        print(f'\nAprobando {usuario["email"]}:', aprobar.json())

    # Listar todos
    usuarios = requests.get(f'{BASE_URL}/admin/usuarios')
    print('\nTodos los usuarios:', usuarios.json())

if __name__ == '__main__':
    admin_email = test_registro_nuevos_usuarios()
    if admin_email:
        test_admin_functions(admin_email)
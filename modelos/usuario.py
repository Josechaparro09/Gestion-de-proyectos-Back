#BACKEND modelos\usuario.py
from datetime import datetime

class Usuario:
    def __init__(self, uid, email, nombre, rol='colaborador'):
        self.uid = uid
        self.email = email
        self.nombre = nombre
        self.rol = rol
        self.fecha_registro = datetime.now()
        self.proyectos = []
        self.activo = True

    def to_dict(self):
        return {
            'uid': self.uid,
            'email': self.email,
            'nombre': self.nombre,
            'rol': self.rol,
            'fecha_registro': self.fecha_registro,
            'proyectos': self.proyectos,
            'activo': self.activo
        }

    @staticmethod
    def from_dict(data):
        usuario = Usuario(
            uid=data.get('uid'),
            email=data.get('email'),
            nombre=data.get('nombre'),
            rol=data.get('rol', 'colaborador')
        )
        usuario.fecha_registro = data.get('fecha_registro', datetime.now())
        usuario.proyectos = data.get('proyectos', [])
        usuario.activo = data.get('activo', True)
        return usuario
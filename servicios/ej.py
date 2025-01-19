from flask import Flask, jsonify, request
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    """
    Endpoint para obtener lista de usuarios
    ---
    responses:
      200:
        description: Lista de usuarios
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              nombre:
                type: string
                example: "Juan"
    """
    usuarios = [
        {"id": 1, "nombre": "Juan"},
        {"id": 2, "nombre": "María"}
    ]
    return jsonify(usuarios)

@app.route('/api/usuarios', methods=['POST'])
def crear_usuario():
    """
    Crea un nuevo usuario
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Pedro"
    responses:
      201:
        description: Usuario creado exitosamente
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 3
            nombre:
              type: string
              example: "Pedro"
    """
    nuevo_usuario = request.json
    # Aquí iría la lógica para crear el usuario
    response = {
        "id": 3,
        "nombre": nuevo_usuario['nombre']
    }
    return jsonify(response), 201

@app.route('/api/usuarios/<int:id>', methods=['GET'])
def obtener_usuario(id):
    """
    Obtiene un usuario por su ID
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Usuario encontrado
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            nombre:
              type: string
              example: "Juan"
      404:
        description: Usuario no encontrado
    """
    # Aquí iría la lógica para buscar el usuario
    usuario = {"id": id, "nombre": "Juan"}
    return jsonify(usuario)

if __name__ == '__main__':
    app.run(debug=True)
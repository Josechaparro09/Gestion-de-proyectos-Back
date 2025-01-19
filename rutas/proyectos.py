# rutas/proyectos.py
from flask import Blueprint, jsonify, request

proyectos_bp = Blueprint('proyectos', __name__)

@proyectos_bp.route('/', methods=['GET'])
def obtener_proyectos():
    return jsonify({"mensaje": "Lista de proyectos"})

@proyectos_bp.route('/', methods=['POST'])
def crear_proyecto():
    return jsonify({"mensaje": "Proyecto creado"})
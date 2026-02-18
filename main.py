from flask_app import app
from flask import request, jsonify


@app.route("/entradas", methods=["POST"])
def recibir_entradas():
    datos = request.json  # Obtener los datos JSON enviados desde el cliente

    # Aquí puedes procesar los datos como desees, por ejemplo, guardarlos en una base de datos
    # por ahora, simplemente los devolveremos para confirmar que se recibieron correctamente
    print("Datos recibidos:", datos)

    # Devolver una respuesta al cliente
    return jsonify({"mensaje": "Datos recibidos correctamente"})


if __name__ == "__main__":
    app.run(debug=True)

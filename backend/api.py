#API para manejar las solicitudes del frontend y comunicarse con Neo4j
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from neo4j import GraphDatabase
from backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

app = Flask(__name__)
CORS(app)


class Neo4JDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_stage_treatment_and_tests(self, t_label, n_label, m_label):
        query = """
        MATCH (n:N_Stage_Finding {label: $n_label})-[:Has_Stage]->(target),
              (m:M_Stage_Finding {label: $m_label})-[:Has_Stage]->(target),
              (t:T_Stage_Finding {label: $t_label})-[:Has_Stage]->(target)
        MATCH (target)-[:Has_Recommended_Test]->(test),
              (target)-[:Has_Treatment_Option]->(treatment)
        RETURN target AS Stage, collect(distinct test.label) AS RecommendedTests, collect(distinct treatment.label) AS TreatmentOptions
        """
        stages = []
        with self.driver.session() as session:
            result = session.run(query, t_label=t_label, n_label=n_label, m_label=m_label)
            for record in result:
                stages.append({
                    "Stage": record["Stage"]["label"],
                    "RecommendedTests": record["RecommendedTests"],
                    "TreatmentOptions": record["TreatmentOptions"]
                })
        return stages if stages else None


# Conectar a base de datos usando configuración
db = Neo4JDatabase(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


# Comprobación simple de conexión al iniciar
try:
    with db.driver.session() as session:
        session.run("RETURN 1")
    print(f"✓ Conectado a Neo4j en {NEO4J_URI} como {NEO4J_USER}")
except Exception as e:
    print("✗ Advertencia: no se pudo conectar a Neo4j:", e)


@app.route('/')
@cross_origin()
def home():
    return "En ejecución"


@app.route('/get_stage_info', methods=['GET'])
@cross_origin()
def get_stage_info():
    t_label = request.args.get('t_label')
    n_label = request.args.get('n_label')
    m_label = request.args.get('m_label')

    if not (t_label and n_label and m_label):
        return jsonify({"error": "Missing parameters"}), 400

    stage_info = db.get_stage_treatment_and_tests(t_label, n_label, m_label)
    if stage_info:
        return jsonify(stage_info)
    else:
        return jsonify({"error": "No results found"}), 404


@app.route('/labels/t', methods=['GET'])
@cross_origin()
def list_t_labels():
    query = "MATCH (n:T_Stage_Finding) RETURN DISTINCT n.label AS label LIMIT 100"
    labels = []
    with db.driver.session() as session:
        result = session.run(query)
        for r in result:
            labels.append(r["label"])
    return jsonify(labels)


@app.route('/labels/n', methods=['GET'])
@cross_origin()
def list_n_labels():
    query = "MATCH (n:N_Stage_Finding) RETURN DISTINCT n.label AS label LIMIT 100"
    labels = []
    with db.driver.session() as session:
        result = session.run(query)
        for r in result:
            labels.append(r["label"])
    return jsonify(labels)


@app.route('/labels/m', methods=['GET'])
@cross_origin()
def list_m_labels():
    query = "MATCH (n:M_Stage_Finding) RETURN DISTINCT n.label AS label LIMIT 100"
    labels = []
    with db.driver.session() as session:
        result = session.run(query)
        for r in result:
            labels.append(r["label"])
    return jsonify(labels)


@app.route('/entradas', methods=['POST'])
@cross_origin()
def recibir_entradas():
    datos = request.get_json(silent=True)
    if datos is None:
        return jsonify({"error": "No JSON body provided"}), 400
    print("Datos recibidos (form):", datos)
    return jsonify({"mensaje": "Datos recibidos correctamente", "datos": datos}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

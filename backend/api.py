#API para manejar las solicitudes del frontend y comunicarse con Neo4j
import json
import threading
import time
import uuid

import pika
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from neo4j import GraphDatabase
from backend.config import (
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    RABBITMQ_URL,
    RECOMMENDATION_REQUEST_QUEUE,
    VALIDATION_RESULT_QUEUE,
)

app = Flask(__name__)
CORS(app)


jobs_store = {}
jobs_lock = threading.Lock()
consumer_thread_started = False


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

        def read_stages(tx):
            result = tx.run(query, t_label=t_label, n_label=n_label, m_label=m_label)
            return [
                {
                    "Stage": record["Stage"]["label"],
                    "RecommendedTests": record["RecommendedTests"],
                    "TreatmentOptions": record["TreatmentOptions"]
                }
                for record in result
            ]

        # execute_read reintenta ante errores transitorios, como la primera consulta
        # tras reiniciar Neo4j (con session.run esa consulta fallaba con un 500)
        with self.driver.session() as session:
            stages = session.execute_read(read_stages)
        return stages if stages else None

    def get_labels(self, node_label):
        query = f"MATCH (n:{node_label}) RETURN DISTINCT n.label AS label LIMIT 100"

        def read_labels(tx):
            return [record["label"] for record in tx.run(query)]

        with self.driver.session() as session:
            return session.execute_read(read_labels)


# Conectar a base de datos usando configuración
db = Neo4JDatabase(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


# Comprobación simple de conexión al iniciar
try:
    with db.driver.session() as session:
        session.run("RETURN 1")
    print(f"✓ Conectado a Neo4j en {NEO4J_URI} como {NEO4J_USER}")
except Exception as e:
    print("✗ Advertencia: no se pudo conectar a Neo4j:", e)


def create_rabbitmq_connection():
    parameters = pika.URLParameters(RABBITMQ_URL)
    parameters.heartbeat = 30
    return pika.BlockingConnection(parameters)


def publish_message(queue_name, payload):
    try:
        connection = create_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
        return True
    except Exception as exc:
        print(f"✗ Error publicando en RabbitMQ ({queue_name}): {exc}")
        return False


def start_validation_result_consumer():
    global consumer_thread_started
    if consumer_thread_started:
        return

    consumer_thread_started = True

    def _worker():
        while True:
            try:
                connection = create_rabbitmq_connection()
                channel = connection.channel()
                channel.queue_declare(queue=VALIDATION_RESULT_QUEUE, durable=True)
                channel.basic_qos(prefetch_count=10)

                print(f"✓ Consumidor escuchando cola: {VALIDATION_RESULT_QUEUE}")

                def on_message(ch, method, properties, body):
                    try:
                        payload = json.loads(body.decode("utf-8"))
                        job_id = payload.get("job_id")
                        if not job_id:
                            raise ValueError("Resultado sin job_id")

                        job = {
                            "status": payload.get("status", "completed"),
                            "updated_at": int(time.time()),
                            "result": payload,
                        }
                        # Los workers publican status "failed" cuando no pueden procesar el trabajo
                        if job["status"] == "failed":
                            job["error"] = payload.get("error", "Error en un microservicio")

                        with jobs_lock:
                            jobs_store[job_id] = job

                        if job["status"] == "failed":
                            print(f"✗ Fallo recibido para job_id={job_id}: {job['error']}")
                        else:
                            print(f"✓ Resultado recibido para job_id={job_id}")
                    except Exception as exc:
                        print(f"✗ Error procesando resultado de validación: {exc}")
                    finally:
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                channel.basic_consume(queue=VALIDATION_RESULT_QUEUE, on_message_callback=on_message)
                channel.start_consuming()
            except Exception as exc:
                print(f"✗ Consumidor desconectado ({VALIDATION_RESULT_QUEUE}): {exc}. Reintentando en 5s...")
                time.sleep(5)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


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


@app.route('/pipeline/submit', methods=['POST'])
@cross_origin()
def submit_pipeline_job():
    data = request.get_json(silent=True) or {}

    t_label = data.get('t_label')
    n_label = data.get('n_label')
    m_label = data.get('m_label')

    if not (t_label and n_label and m_label):
        tnm = data.get('tnm', {})
        t_label = t_label or tnm.get('t_label')
        n_label = n_label or tnm.get('n_label')
        m_label = m_label or tnm.get('m_label')

    if not (t_label and n_label and m_label):
        return jsonify({"error": "Missing TNM parameters"}), 400

    job_id = str(uuid.uuid4())
    message = {
        "job_id": job_id,
        "tnm": {
            "t_label": t_label,
            "n_label": n_label,
            "m_label": m_label,
        },
        "context": data.get("context", {}),
        "timestamp": int(time.time()),
    }

    with jobs_lock:
        jobs_store[job_id] = {
            "status": "queued",
            "created_at": int(time.time()),
        }

    published = publish_message(RECOMMENDATION_REQUEST_QUEUE, message)
    if not published:
        with jobs_lock:
            jobs_store[job_id] = {
                "status": "failed",
                "updated_at": int(time.time()),
                "error": "No se pudo publicar el trabajo en el broker",
            }
        return jsonify({"error": "Message broker unavailable", "job_id": job_id}), 503

    with jobs_lock:
        jobs_store[job_id]["status"] = "processing"
        jobs_store[job_id]["updated_at"] = int(time.time())

    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "message": "Trabajo enviado a microservicios",
    }), 202


@app.route('/pipeline/result/<job_id>', methods=['GET'])
@cross_origin()
def get_pipeline_result(job_id):
    with jobs_lock:
        job = jobs_store.get(job_id)

    if not job:
        return jsonify({"error": "job_id not found"}), 404

    response = {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
    }

    if "error" in job:
        response["error"] = job["error"]

    if "result" in job:
        response["result"] = job["result"]

    return jsonify(response), 200


@app.route('/pipeline/health', methods=['GET'])
@cross_origin()
def pipeline_health():
    rabbitmq_ok = False
    try:
        connection = create_rabbitmq_connection()
        connection.close()
        rabbitmq_ok = True
    except Exception:
        rabbitmq_ok = False

    return jsonify({
        "rabbitmq": "up" if rabbitmq_ok else "down",
        "consumer": "running" if consumer_thread_started else "stopped",
        "queues": {
            "recommendation_request": RECOMMENDATION_REQUEST_QUEUE,
            "validation_result": VALIDATION_RESULT_QUEUE,
        },
    })


@app.route('/labels/t', methods=['GET'])
@cross_origin()
def list_t_labels():
    return jsonify(db.get_labels("T_Stage_Finding"))


@app.route('/labels/n', methods=['GET'])
@cross_origin()
def list_n_labels():
    return jsonify(db.get_labels("N_Stage_Finding"))


@app.route('/labels/m', methods=['GET'])
@cross_origin()
def list_m_labels():
    return jsonify(db.get_labels("M_Stage_Finding"))


@app.route('/pipeline/debug', methods=['GET'])
@cross_origin()
def pipeline_debug():
    """Endpoint de debug para ver estado de todos los jobs"""
    with jobs_lock:
        jobs_snapshot = dict(jobs_store)
    
    return jsonify({
        "total_jobs": len(jobs_snapshot),
        "jobs": jobs_snapshot,
        "timestamp": int(time.time())
    }), 200


@app.route('/entradas', methods=['POST'])
@cross_origin()
def recibir_entradas():
    datos = request.get_json(silent=True)
    if datos is None:
        return jsonify({"error": "No JSON body provided"}), 400
    print("Datos recibidos (form):", datos)
    return jsonify({"mensaje": "Datos recibidos correctamente", "datos": datos}), 201


# El servidor se arranca con backend/run_waitress.py; el consumidor se inicia al importar el módulo.
start_validation_result_consumer()

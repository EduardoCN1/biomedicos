import json
import time
from typing import Any, Dict, List

import pika
from neo4j import GraphDatabase

from backend.config import (
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    RABBITMQ_URL,
    RECOMMENDATION_REQUEST_QUEUE,
    VALIDATION_REQUEST_QUEUE,
)


class Neo4JDatabase:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_stage_treatment_and_tests(self, t_label: str, n_label: str, m_label: str):
        query = """
        MATCH (n:N_Stage_Finding {label: $n_label})-[:Has_Stage]->(target),
              (m:M_Stage_Finding {label: $m_label})-[:Has_Stage]->(target),
              (t:T_Stage_Finding {label: $t_label})-[:Has_Stage]->(target)
        MATCH (target)-[:Has_Recommended_Test]->(test),
              (target)-[:Has_Treatment_Option]->(treatment)
        RETURN target AS Stage,
               collect(distinct test.label) AS RecommendedTests,
               collect(distinct treatment.label) AS TreatmentOptions
        """

        stages: List[Dict[str, Any]] = []
        with self.driver.session() as session:
            result = session.run(query, t_label=t_label, n_label=n_label, m_label=m_label)
            for record in result:
                stages.append(
                    {
                        "Stage": record["Stage"]["label"],
                        "RecommendedTests": record["RecommendedTests"],
                        "TreatmentOptions": record["TreatmentOptions"],
                    }
                )

        return stages


def create_connection() -> pika.BlockingConnection:
    parameters = pika.URLParameters(RABBITMQ_URL)
    parameters.heartbeat = 30
    return pika.BlockingConnection(parameters)


def publish(channel, queue_name: str, payload: Dict[str, Any]) -> None:
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )


def run() -> None:
    db = Neo4JDatabase(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    while True:
        try:
            connection = create_connection()
            channel = connection.channel()
            channel.queue_declare(queue=RECOMMENDATION_REQUEST_QUEUE, durable=True)
            channel.queue_declare(queue=VALIDATION_REQUEST_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            print(f"[recommender] Esperando mensajes en: {RECOMMENDATION_REQUEST_QUEUE}")

            def on_message(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                    job_id = payload.get("job_id")
                    tnm = payload.get("tnm", {})
                    t_label = tnm.get("t_label")
                    n_label = tnm.get("n_label")
                    m_label = tnm.get("m_label")

                    if not (job_id and t_label and n_label and m_label):
                        raise ValueError("Mensaje inválido: faltan job_id o TNM")

                    recommendations = db.get_stage_treatment_and_tests(t_label, n_label, m_label)

                    validation_payload = {
                        "job_id": job_id,
                        "tnm": tnm,
                        "recommendations": recommendations,
                        "context": payload.get("context", {}),
                        "timestamp": int(time.time()),
                    }

                    publish(ch, VALIDATION_REQUEST_QUEUE, validation_payload)
                    print(f"[recommender] job_id={job_id} enviado a validación")
                except Exception as exc:
                    print(f"[recommender] Error procesando mensaje: {exc}")
                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=RECOMMENDATION_REQUEST_QUEUE, on_message_callback=on_message)
            channel.start_consuming()

        except Exception as exc:
            print(f"[recommender] Broker desconectado o error: {exc}. Reintentando en 5s...")
            time.sleep(5)
        finally:
            try:
                db.close()
            except Exception:
                pass


if __name__ == "__main__":
    run()

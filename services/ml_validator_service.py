import json
import time
from typing import Any, Dict, List

import pika

from backend.config import (
    RABBITMQ_URL,
    VALIDATION_REQUEST_QUEUE,
    VALIDATION_RESULT_QUEUE,
)


REJECTION_KEYWORDS = {"experimental", "no recomendado", "descartar"}


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


def evaluate_treatment(option: str) -> Dict[str, Any]:
    normalized = (option or "").strip().lower()
    rejected = any(keyword in normalized for keyword in REJECTION_KEYWORDS)
    approved = not rejected
    confidence = 0.78 if approved else 0.42
    reason = "Aprobado por validador mock" if approved else "Descartado por regla mock"

    return {
        "option": option,
        "approved": approved,
        "confidence": confidence,
        "reason": reason,
    }


def validate_recommendations(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    final_recommendations: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    approved_count = 0
    rejected_count = 0

    for item in recommendations or []:
        stage = item.get("Stage")
        tests = item.get("RecommendedTests", [])
        options = item.get("TreatmentOptions", [])

        evaluated_options = [evaluate_treatment(option) for option in options]
        approved_options = [entry["option"] for entry in evaluated_options if entry["approved"]]

        approved_count += len(approved_options)
        rejected_count += len(options) - len(approved_options)

        if not approved_options:
            approved_options = options[:1]

        final_recommendations.append(
            {
                "Stage": stage,
                "RecommendedTests": tests,
                "TreatmentOptions": approved_options,
            }
        )

        details.append(
            {
                "stage": stage,
                "evaluations": evaluated_options,
            }
        )

    return {
        "final_recommendations": final_recommendations,
        "validation_details": details,
        "summary": {
            "approved_count": approved_count,
            "rejected_count": rejected_count,
        },
    }


def run() -> None:
    while True:
        try:
            connection = create_connection()
            channel = connection.channel()
            channel.queue_declare(queue=VALIDATION_REQUEST_QUEUE, durable=True)
            channel.queue_declare(queue=VALIDATION_RESULT_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            print(f"[ml-validator] Esperando mensajes en: {VALIDATION_REQUEST_QUEUE}")

            def on_message(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                    job_id = payload.get("job_id")
                    recommendations = payload.get("recommendations", [])

                    if not job_id:
                        raise ValueError("Mensaje inválido: falta job_id")

                    validation_result = validate_recommendations(recommendations)

                    output = {
                        "job_id": job_id,
                        "status": "completed",
                        "tnm": payload.get("tnm", {}),
                        "recommendations": recommendations,
                        "final_recommendations": validation_result["final_recommendations"],
                        "validation_details": validation_result["validation_details"],
                        "summary": validation_result["summary"],
                        "model": {
                            "name": "mock-validator",
                            "version": "0.1.0",
                            "note": "Reemplazar por servicio ML real",
                        },
                        "timestamp": int(time.time()),
                    }

                    publish(ch, VALIDATION_RESULT_QUEUE, output)
                    print(f"[ml-validator] job_id={job_id} validado y publicado")
                except Exception as exc:
                    print(f"[ml-validator] Error procesando mensaje: {exc}")
                finally:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=VALIDATION_REQUEST_QUEUE, on_message_callback=on_message)
            channel.start_consuming()

        except Exception as exc:
            print(f"[ml-validator] Broker desconectado o error: {exc}. Reintentando en 5s...")
            time.sleep(5)


if __name__ == "__main__":
    run()

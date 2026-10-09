"""
Script para importar datos desde CSV a Neo4j
Uso: python scripts/import_csv.py

En Docker lo ejecuta automáticamente el servicio 'seed' cada vez que se levanta el proyecto.
Si la base de datos ya tiene datos no importa nada, así que es seguro ejecutarlo varias veces.
Para recargar los datos desde cero (borra el volumen de Neo4j): docker compose down -v

Antes de importar valida el formato de los datos (ver validate_nodes); si no es correcto
no importa nada y termina con error, para que los datos se corrijan en el CSV.
"""

import csv
import json
import os
import sys

from neo4j import GraphDatabase

# Agregar parent directory al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def read_json_column(path):
    """Lee un CSV de una sola columna cuyas celdas son objetos JSON (formato de exportación de Neo4j)"""
    with open(path, encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Encabezado: "n" o "r"
        return [json.loads(row[0]) for row in reader if row]


def load_data_from_csv(data_dir='data'):
    """Carga datos desde archivos CSV"""
    try:
        nodos_path = os.path.join(data_dir, 'nodos.csv')
        relaciones_path = os.path.join(data_dir, 'relaciones.csv')

        if not os.path.exists(nodos_path):
            print(f"[ERROR] Archivo no encontrado: {nodos_path}")
            return None, None
        if not os.path.exists(relaciones_path):
            print(f"[ERROR] Archivo no encontrado: {relaciones_path}")
            return None, None

        print(f"[✓] Cargando nodos desde: {nodos_path}")
        nodes = read_json_column(nodos_path)

        print(f"[✓] Cargando relaciones desde: {relaciones_path}")
        relations = read_json_column(relaciones_path)

        return nodes, relations
    except Exception as e:
        print(f"[ERROR] Al cargar CSV: {e}")
        return None, None


def validate_nodes(nodes):
    """Devuelve los errores de formato de los nodos (lista vacía si todo es correcto).

    Regla: la propiedad 'label' de cada nodo debe ser texto. Las exportaciones de la
    ontología a veces la guardan como lista (["Stage IIA"]); en ese caso la API devolvería
    listas y las búsquedas por nombre en Neo4j no encontrarían el nodo.
    """
    errors = []
    for node in nodes:
        label = node['properties'].get('label')
        if not isinstance(label, str) or not label.strip():
            errors.append(f"nodo id={node['id']}: label={json.dumps(label, ensure_ascii=False)}")
    return errors


def create_graph(tx, nodes, relations):
    """Crea nodos y relaciones; el id original se guarda en neo4j_id para enlazar las relaciones"""
    for node in nodes:
        labels = ":".join(f"`{label}`" for label in node['labels'])
        tx.run(
            f"CREATE (n:{labels}) SET n = $props, n.neo4j_id = $id",
            props=node['properties'],
            id=node['id'],
        )

    for relation in relations:
        tx.run(
            f"MATCH (a {{neo4j_id: $start}}), (b {{neo4j_id: $end}}) "
            f"CREATE (a)-[r:`{relation['type']}`]->(b) SET r = $props",
            start=relation['start'],
            end=relation['end'],
            props=relation['properties'],
        )


def import_to_neo4j(nodes, relations):
    """Importa datos a Neo4j en una sola transacción: si algo falla no queda nada a medias"""
    driver = None
    try:
        print(f"\n[→] Conectando a Neo4j: {NEO4J_URI}")
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"[✓] Conexión exitosa a Neo4j")

        with driver.session() as session:
            existing = session.run("MATCH (n) RETURN count(n) AS total").single()["total"]
            if existing > 0:
                print(f"[✓] La base de datos ya tiene {existing} nodos; no se importa nada")
                return

            print(f"\n[→] Importando {len(nodes)} nodos y {len(relations)} relaciones...")
            session.execute_write(create_graph, nodes, relations)

        print(f"[✓] Datos importados exitosamente a Neo4j")

    except Exception as e:
        print(f"[ERROR] Al importar a Neo4j: {e}")
        sys.exit(1)
    finally:
        if driver is not None:
            driver.close()


def main():
    """Función principal"""
    print("=" * 60)
    print("Script de Importación de Datos CSV → Neo4j")
    print("=" * 60)

    # Cargar CSV
    nodes, relations = load_data_from_csv()
    if nodes is None or relations is None:
        sys.exit(1)

    print(f"\nDatos cargados:")
    print(f"  - Nodos: {len(nodes)}")
    print(f"  - Relaciones: {len(relations)}")

    # Validar formato antes de tocar Neo4j
    errors = validate_nodes(nodes)
    if errors:
        print(f"\n[ERROR] {len(errors)} nodo(s) de data/nodos.csv con 'label' que no es texto:")
        for error in errors[:10]:
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... y {len(errors) - 10} más")
        print('\nCorrige el CSV: "label" debe ser texto, por ejemplo "label":"Stage IIA"')
        print('en lugar de "label":["Stage IIA"]. Ver docs/DATABASE.md (Formato de los datos).')
        print("No se ha importado nada.")
        sys.exit(1)
    print(f"[✓] Formato de los datos correcto")

    # Importar a Neo4j
    import_to_neo4j(nodes, relations)

    print("\n" + "=" * 60)
    print("Importación completada")
    print("=" * 60)


if __name__ == '__main__':
    main()

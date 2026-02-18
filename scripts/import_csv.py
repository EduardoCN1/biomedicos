"""
Script para importar datos desde CSV a Neo4j
Uso: python scripts/import_csv.py

Nota: Solo utilizar para cargar datos iniciales en la base de datos en caso de que esté vacia o quiera cargar nuevos datos.
Precaución: Si la base de datos ya tiene datos, este ecript puede duplicar datos y se tendrá que hacer una limpieza manual.
"""

import os
import sys
import pandas as pd
from py2neo import Graph, Node, Relationship

# Agregar parent directory al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

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
        df_nodes = pd.read_csv(nodos_path, converters={'n': eval})
        
        print(f"[✓] Cargando relaciones desde: {relaciones_path}")
        df_relations = pd.read_csv(relaciones_path, converters={'r': eval})
        
        return df_nodes, df_relations
    except Exception as e:
        print(f"[ERROR] Al cargar CSV: {e}")
        return None, None

def import_to_neo4j(df_nodes, df_relations):
    """Importa datos a Neo4j"""
    try:
        print(f"\n[→] Conectando a Neo4j: {NEO4J_URI}")
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Test de conexión
        graph.database.name
        print(f"[✓] Conexión exitosa a Neo4j")
        
        # Diccionario para mapear IDs
        nodes_dict = {}
        
        # Importar nodos
        print(f"\n[→] Importando {len(df_nodes)} nodos...")
        for idx, row in df_nodes.iterrows():
            node_info = row['n']
            node = Node(*node_info['labels'], **node_info['properties'])
            node['neo4j_id'] = node_info['id']
            graph.create(node)
            nodes_dict[node_info['id']] = node
            if (idx + 1) % 10 == 0:
                print(f"   [{idx + 1}/{len(df_nodes)}] nodos importados")
        
        print(f"[✓] {len(df_nodes)} nodos importados correctamente")
        
        # Importar relaciones
        print(f"\n[→] Importando {len(df_relations)} relaciones...")
        for idx, row in df_relations.iterrows():
            relation_info = row['r']
            start_node = nodes_dict[relation_info['start']]
            end_node = nodes_dict[relation_info['end']]
            relationship = Relationship(start_node, relation_info['type'], end_node, **relation_info['properties'])
            graph.create(relationship)
            if (idx + 1) % 10 == 0:
                print(f"   [{idx + 1}/{len(df_relations)}] relaciones importadas")
        
        print(f"[✓] {len(df_relations)} relaciones importadas correctamente")
        print(f"\n[✓] Datos importados exitosamente a Neo4j")
        
    except Exception as e:
        print(f"[ERROR] Al importar a Neo4j: {e}")
        sys.exit(1)

def main():
    """Función principal"""
    print("=" * 60)
    print("Script de Importación de Datos CSV → Neo4j")
    print("=" * 60)
    
    # Cargar CSV
    df_nodes, df_relations = load_data_from_csv()
    if df_nodes is None or df_relations is None:
        sys.exit(1)
    
    print(f"\nDatos cargados:")
    print(f"  - Nodos: {len(df_nodes)}")
    print(f"  - Relaciones: {len(df_relations)}")
    
    # Importar a Neo4j
    import_to_neo4j(df_nodes, df_relations)
    
    print("\n" + "=" * 60)
    print("Importación completada")
    print("=" * 60)

if __name__ == '__main__':
    main()

"""
Configuración centralizada de la aplicación.
Lee variables de entorno para Neo4j y servidor.
-Nota: Debe configurar su .env con las variables que se indican aquí, en caso de que no exista se utilizan 
valor por defecto.
"""
import os

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

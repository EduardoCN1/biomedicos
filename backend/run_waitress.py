import os
import sys

# Agregar directorio raíz al path para que encuentre el módulo backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from waitress import serve
from backend.api import app

# Leer host/port desde variables de entorno para facilitar pruebas
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "5000"))

print(f"✓ Servidor Waitress iniciado en http://{host}:{port}")
print(f"  Presiona Ctrl+C para detener\n")

serve(app, host=host, port=port)
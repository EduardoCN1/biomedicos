"""
Tests básicos para la API.
Ejecutar con: python -m pytest tests/test_api.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.api import app, db


@pytest.fixture
def client():
    """Cliente de prueba para Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPI:
    """Pruebas para los endpoints de la API."""

    def test_home(self, client):
        """GET / debe devolver 'En ejecución'."""
        response = client.get('/')
        assert response.status_code == 200
        assert response.get_data(as_text=True) == "En ejecución"

    def test_get_stage_info_missing_params(self, client):
        """GET /get_stage_info sin parámetros debe devolver 400."""
        response = client.get('/get_stage_info')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "Missing parameters"

    def test_get_stage_info_with_params(self, client):
        """GET /get_stage_info con parámetros debe devolver lista (o 404 si no hay datos)."""
        response = client.get('/get_stage_info?t_label=T2&n_label=N1&m_label=M0')
        # Puede ser 200 (si hay datos) o 404 (sin datos)
        assert response.status_code in [200, 404]
        data = response.get_json()
        assert isinstance(data, (list, dict))

    def test_labels_t(self, client):
        """GET /labels/t debe devolver lista de etiquetas."""
        response = client.get('/labels/t')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_labels_n(self, client):
        """GET /labels/n debe devolver lista de etiquetas."""
        response = client.get('/labels/n')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_labels_m(self, client):
        """GET /labels/m debe devolver lista de etiquetas."""
        response = client.get('/labels/m')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_post_entradas(self, client):
        """POST /entradas con JSON debe devolver confirmación."""
        payload = {"name": "Prueba", "age": 30}
        response = client.post('/entradas', json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert 'mensaje' in data
        assert data['mensaje'] == "Datos recibidos correctamente"

    def test_post_entradas_no_json(self, client):
        """POST /entradas sin JSON debe devolver 400."""
        response = client.post('/entradas', data='not json')
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

import unittest
from unittest.mock import patch

from app import app
from app.servicios import ErrorDatos


class PruebasFavoritos(unittest.TestCase):
    def setUp(self):
        configuracion = patch.dict(app.config, {
            'TESTING': True, 'SECRET_KEY': 'prueba-favoritos',
            'SUPABASE_URL': '', 'SUPABASE_SECRET_KEY': '',
        })
        configuracion.start()
        self.addCleanup(configuracion.stop)
        self.cliente = app.test_client()
        with self.cliente.session_transaction() as sesion:
            sesion['csrf'] = 'prueba'

    def agregar(self, identificador='futbol'):
        return self.cliente.post(
            f'/favoritos/{identificador}/agregar', data={'csrf': 'prueba'},
        )

    def test_agregar_consultar_quitar(self):
        self.assertIn('Todavía no tienes favoritos',
                      self.cliente.get('/favoritos').text)
        self.assertEqual(self.agregar().status_code, 302)
        pagina = self.cliente.get('/favoritos')
        self.assertIn('Fútbol', pagina.text)
        self.assertIn('/deportes/futbol', pagina.text)
        self.assertIn('Demostración', pagina.text)
        self.assertIn('Quitar de favoritos', self.cliente.get('/').text)
        self.cliente.post('/favoritos/futbol/quitar', data={'csrf': 'prueba'})
        self.assertIn('Todavía no tienes favoritos',
                      self.cliente.get('/favoritos').text)

    def test_no_duplica_y_aisla_navegadores(self):
        self.agregar()
        self.agregar()
        with self.cliente.session_transaction() as sesion:
            self.assertEqual(sesion['favoritos_demostracion'], ['futbol'])
        otro = app.test_client()
        self.assertIn('Todavía no tienes favoritos', otro.get('/favoritos').text)

    def test_csrf_y_metodos(self):
        for accion in ('agregar', 'quitar'):
            ruta = f'/favoritos/futbol/{accion}'
            self.assertEqual(self.cliente.get(ruta).status_code, 405)
            self.assertEqual(self.cliente.post(ruta).status_code, 400)

    def test_no_agrega_deporte_inexistente(self):
        self.assertEqual(self.agregar('inexistente').status_code, 404)
        with self.cliente.session_transaction() as sesion:
            self.assertNotIn('favoritos_demostracion', sesion)

    def test_error_no_borra_y_permite_quitar_sin_conexion(self):
        self.agregar()
        with patch('app.favoritos.obtener_deporte', side_effect=ErrorDatos('Error')):
            self.assertEqual(self.cliente.get('/favoritos').status_code, 503)
            with self.cliente.session_transaction() as sesion:
                self.assertEqual(sesion['favoritos_demostracion'], ['futbol'])
            respuesta = self.cliente.post('/favoritos/futbol/quitar',
                                          data={'csrf': 'prueba'})
            self.assertEqual(respuesta.status_code, 302)

    def test_limite_y_deporte_retirado(self):
        with self.cliente.session_transaction() as sesion:
            sesion['favoritos_demostracion'] = [f'deporte-{i}' for i in range(20)]
        self.agregar()
        with self.cliente.session_transaction() as sesion:
            self.assertEqual(len(sesion['favoritos_demostracion']), 20)
            self.assertNotIn('futbol', sesion['favoritos_demostracion'])
        pagina = self.cliente.get('/favoritos')
        self.assertEqual(pagina.status_code, 200)
        self.assertIn('no está disponible', pagina.text)

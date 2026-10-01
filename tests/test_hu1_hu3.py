import re
import unittest
from unittest.mock import patch

from itsdangerous import SignatureExpired

from app import app
from app.comparacion import firmador_comparacion, preparar_resumen
from app.deportes import validar_datos
from app.servicios import ErrorDatos


class PruebasCondicionesComparacion(unittest.TestCase):
    def setUp(self):
        self.configuracion = patch.dict(app.config, {
            'TESTING': True, 'SECRET_KEY': 'prueba-historias',
            'SUPABASE_URL': '', 'SUPABASE_SECRET_KEY': '',
        })
        self.configuracion.start()
        self.addCleanup(self.configuracion.stop)
        self.cliente = app.test_client()
        self.deporte = {
            'identificador': 'futbol', 'nombre': 'Fútbol',
            'costo_estimado': '90.50', 'moneda': 'BOB',
            'periodo_costo': 'Por mes', 'equipamiento': 'Balón y calzado',
            'tiempo_practica': 'Tres sesiones por semana',
            'espacio_practica': 'exterior',
            'instalaciones_especiales': 'si', 'requiere_companeros': 'no',
        }

    def token(self):
        with self.cliente.session_transaction() as sesion:
            sesion['csrf'] = 'prueba'
        return 'prueba'

    def test_condiciones_muestran_si_no_y_pendiente(self):
        with patch('app.deportes.obtener_deporte', return_value=self.deporte):
            respuesta = self.cliente.get('/deportes/futbol')
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn('<dd>Exteriores</dd>', respuesta.text)
            self.assertIn('<dd>Sí</dd>', respuesta.text)
            self.assertIn('<dd>No</dd>', respuesta.text)
        respuesta = self.cliente.get('/deportes/futbol')
        self.assertIn('Información pendiente', respuesta.text)
        self.assertNotIn('<dd>No</dd>', respuesta.text)

    def test_validar_y_guardar_condiciones(self):
        datos = validar_datos(self.deporte)
        self.assertEqual(datos['espacio_practica'], 'exterior')
        self.assertEqual(datos['requiere_companeros'], 'no')
        datos = validar_datos(self.deporte | {'requiere_companeros': ''})
        self.assertIsNone(datos['requiere_companeros'])
        for campo in ('espacio_practica', 'requiere_companeros',
                      'instalaciones_especiales'):
            with self.assertRaises(ValueError):
                validar_datos(self.deporte | {campo: 'inventado'})

    def test_edicion_envia_campos_hu1_a_supabase(self):
        app.config.update(SUPABASE_URL='https://prueba.supabase.co',
                          SUPABASE_SECRET_KEY='sb_secret_prueba')
        self.token()
        with self.cliente.session_transaction() as sesion:
            sesion['administrador'] = True
        with patch('app.deportes.consultar', return_value=[self.deporte]) as consulta:
            respuesta = self.cliente.post('/admin/deportes/futbol/editar',
                data=self.deporte | {'csrf': 'prueba'})
            self.assertEqual(respuesta.status_code, 302)
            self.assertEqual(consulta.call_args.kwargs['datos']['requiere_companeros'], 'no')

    def test_comparacion_sin_seleccion_o_con_un_deporte(self):
        for ruta in ('/comparar', '/comparar?deporte=futbol'):
            respuesta = self.cliente.get(ruta)
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotIn('Descargar comparación en PDF', respuesta.text)

    def test_comparacion_dos_y_tres_deportes(self):
        for cantidad in (2, 3):
            ids = ['futbol', 'natacion', 'tenis'][:cantidad]
            respuesta = self.cliente.get('/comparar', query_string={'deporte': ids})
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn('Descargar comparación en PDF', respuesta.text)
            firma = re.search(r'name="comparacion" value="([^"]+)"', respuesta.text).group(1)
            with app.app_context():
                documento = firmador_comparacion().loads(firma)
            self.assertEqual(len(documento['deportes']), cantidad)
            self.assertTrue(documento['provisional'])

    def test_rechaza_seleccion_invalida(self):
        for ids in (['futbol', 'futbol'], ['futbol', 'tenis', 'natacion', 'baloncesto'], ['a,b']):
            self.assertEqual(self.cliente.get('/comparar', query_string={'deporte': ids}).status_code, 400)
        self.assertEqual(self.cliente.get('/comparar?deporte=inexistente').status_code, 404)
        self.assertEqual(self.cliente.get('/comparar?pagina=abc').status_code, 400)

    def test_pdf_refleja_consulta_sin_volver_a_leer_datos(self):
        natacion = self.deporte | {'nombre': 'Natación', 'identificador': 'natacion'}
        with patch('app.comparacion.obtener_deporte', side_effect=[self.deporte, natacion]):
            pagina = self.cliente.get('/comparar?deporte=futbol&deporte=natacion')
        firma = re.search(r'name="comparacion" value="([^"]+)"', pagina.text).group(1)
        with patch('app.comparacion.obtener_deporte') as consultar:
            respuesta = self.cliente.post('/comparar/descargar', data={
                'csrf': self.token(), 'comparacion': firma})
            self.assertEqual(respuesta.status_code, 200)
            self.assertEqual(respuesta.mimetype, 'application/pdf')
            self.assertTrue(respuesta.data.startswith(b'%PDF-'))
            self.assertIn('attachment', respuesta.headers['Content-Disposition'])
            consultar.assert_not_called()
        documento = firmador_comparacion().loads(firma)
        self.assertIn('90.50 BOB', documento['deportes'][0]['campos'][0][1])

    def test_descarga_rechaza_csrf_firma_invalida_y_vencimiento(self):
        self.assertEqual(self.cliente.get('/comparar/descargar').status_code, 405)
        self.assertEqual(self.cliente.post('/comparar/descargar').status_code, 400)
        self.assertEqual(self.cliente.post('/comparar/descargar', data={
            'csrf': self.token(), 'comparacion': 'alterado'}).status_code, 400)
        with patch('app.comparacion.firmador_comparacion') as firmador:
            firmador.return_value.loads.side_effect = SignatureExpired('vencido')
            respuesta = self.cliente.post('/comparar/descargar', data={
                'csrf': self.token(), 'comparacion': 'vencido'})
            self.assertEqual(respuesta.status_code, 400)
            self.assertIn('descarga venció', respuesta.text)

    def test_fallo_supabase_no_genera_comparacion_inventada(self):
        app.config.update(SUPABASE_URL='https://prueba.supabase.co',
                          SUPABASE_SECRET_KEY='sb_secret_prueba')
        with patch('app.comparacion.consultar', side_effect=ErrorDatos('Error de conexión')):
            respuesta = self.cliente.get('/comparar?deporte=futbol&deporte=natacion')
            self.assertEqual(respuesta.status_code, 503)
            self.assertNotIn('Descargar comparación en PDF', respuesta.text)

    def test_mantiene_seleccion_de_otra_pagina(self):
        app.config.update(SUPABASE_URL='https://prueba.supabase.co',
                          SUPABASE_SECRET_KEY='sb_secret_prueba')
        with patch('app.comparacion.consultar', return_value=[{'nombre': 'Tenis', 'identificador': 'tenis'}]), patch('app.comparacion.obtener_deporte', return_value=self.deporte):
            respuesta = self.cliente.get('/comparar?pagina=2&deporte=futbol')
            self.assertIn('value="futbol" checked', respuesta.text)
            self.assertIn('Tenis', respuesta.text)

    def test_costo_cero_no_se_muestra_como_pendiente(self):
        resumen = preparar_resumen([self.deporte | {'costo_estimado': 0}])
        self.assertIn('0 BOB', resumen[0]['campos'][0][1])


if __name__ == '__main__':
    unittest.main()

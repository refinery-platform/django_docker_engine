import unittest

from django.test import Client

class DemoPathRoutingTests(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_home(self):
        response = self.client.get('/?uploaded=3x3.csv')
        context = response.context

        fields = context['launch_form'].fields
        self.assertEqual({'container_name', 'data', 'tool'}, fields.keys())

        self.assertIn(('3x3.csv', '3x3.csv'), fields['data'].choices)
        # Locally, you may also have data choices which are not checked in.

        self.assertEquals(
            [('debugger', 'debugger'),
             ('lineup', 'lineup'),
             ('heatmap', 'heatmap')],
            fields['tool'].choices)

        self.assertEqual(
            context['launch_form'].initial,
            {'data': '3x3.csv'})

        content = response.content.decode('utf-8')
        self.assertIn('<option value="3x3.csv" selected>', content)
        self.assertIn('<option value="debugger">debugger</option>', content)


    def test_lauch(self):
        pass

    def test_kill(self):
        pass

    def test_upload(self):
        pass

    def test_docker(self):
        pass
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class ErrorsURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')

    def test_urls_404_correct_template(self):
        """Cтраница 404 отдает кастомный шаблон."""
        address = '/page404/'
        template = 'core/404.html'
        response = self.guest_client.get(address)
        self.assertTemplateUsed(response, template)

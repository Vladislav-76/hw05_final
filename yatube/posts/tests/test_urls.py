from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_URL_exists_at_desired_location(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestName'),
            text='Тестовый текст',
            pk=2128,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user = PostURLTest.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_post_url_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        url_names = [
            '/',
            '/group/test-slug/',
            '/profile/TestName/',
            '/posts/2128/',
            '/unexisting_page/',
            '/posts/2128/edit/',
            '/create/']
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if address == '/unexisting_page/':
                    self.assertEqual(response.status_code, 404)
                elif (address == '/posts/2128/edit/' or address == '/create/'):
                    self.assertRedirects(
                        response, f'/auth/login/?next={address}')
                else:
                    self.assertEqual(response.status_code, 200)

    def test_post_url_exists_at_desired_location_authorized(self):
        """Страницы доступные авторизированному пользователю."""
        url_names = [
            '/',
            '/group/test-slug/',
            '/profile/TestName/',
            '/posts/2128/',
            '/posts/2128/edit/',
            '/create/'
        ]
        for address in url_names:
            with self.subTest(address=address):
                if address == '/posts/2128/edit/':
                    response = self.authorized_client_author.get(address)
                else:
                    response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestName/': 'posts/profile.html',
            '/posts/2128/': 'posts/post_detail.html',
            '/posts/2128/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

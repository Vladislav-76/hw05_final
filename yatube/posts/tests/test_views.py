import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.models import Post, Group, Comment, Follow
from django import forms

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group = Group.objects.create(
            title='Другая группа',
            slug='test-slug_dif',
            description='Тестовое описание другое',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='TestName'),
            text='Тестовый текст',
            pk=2128,
            group=Group.objects.get(title='Тестовая группа'),
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            author=User.objects.create_user(username='TestCommentor'),
            text='Тестовый комментарий',
            post=Post.objects.get(pk=2128)
        )
        cls.follow = Follow.objects.create(
            user=User.objects.create_user(username='Follower'),
            author=User.objects.create_user(username='Following'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.user = PostPagesTest.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.test_user = User.objects.get(username='TestCommentor')
        self.authorized_client_test_user = Client()
        self.authorized_client_test_user.force_login(self.test_user)
        self.follower = User.objects.get(username='Follower')
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'TestName'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 2128}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 2128}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_page1(self, template):
        response = self.authorized_client_author.get(template)
        first_post = response.context['page_obj'][0]
        value = dict()
        value['post_text_0'] = first_post.text
        value['post_author_0'] = first_post.author.username
        value['post_group_0'] = first_post.group.title
        value['post_image_0'] = first_post.image
        return value

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        context = self.context_page1(reverse('posts:index'))
        self.assertEqual(context['post_text_0'], 'Тестовый текст')
        self.assertEqual(context['post_author_0'], 'TestName')
        self.assertEqual(context['post_group_0'], 'Тестовая группа')
        self.assertEqual(context['post_image_0'], 'posts/small.gif')

    def test_index_cache(self):
        """Проверка работы кеша"""
        Post.objects.create(
            author=User.objects.get(username='TestName'),
            text='Тест кеша'
        )
        response_before_delete = self.client.get(reverse('posts:index'))
        self.assertContains(response_before_delete, 'Тест кеша')
        Post.objects.filter(text='Тест кеша').delete()
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, response_before_delete.content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotContains(response, response_before_delete.content)

    def test_group_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        context = self.context_page1(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertEqual(context['post_text_0'], 'Тестовый текст')
        self.assertEqual(context['post_group_0'], 'Тестовая группа')
        self.assertEqual(context['post_image_0'], 'posts/small.gif')
        response = self.authorized_client_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug_dif'}))
        self.assertEqual(len(response.context.get('page_obj')), 0)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        context = self.context_page1(
            reverse('posts:profile', kwargs={'username': 'TestName'}))
        self.assertEqual(context['post_text_0'], 'Тестовый текст')
        self.assertEqual(context['post_author_0'], 'TestName')
        self.assertEqual(context['post_group_0'], 'Тестовая группа')
        self.assertEqual(context['post_image_0'], 'posts/small.gif')

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': 2128}))
        self.assertEqual(response.context.get('post').text, 'Тестовый текст')
        self.assertEqual(response.context.get('post').pk, 2128)
        self.assertEqual(
            response.context.get('post').image, 'posts/small.gif')

    def test_comment_correct_context(self):
        """Шаблон post_detail сформирован с комментарием."""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': 2128}))
        first_comment = response.context['comments'][0]
        self.assertEqual(first_comment.text, 'Тестовый комментарий')

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильными полями."""
        response = self.authorized_client_author.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_create_edit сформирован с правильными полями."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': 2128}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post_id'), 2128)

    def test_follow_create_correct(self):
        """Авторизованный пользователь может подписываться."""
        follows_count = Follow.objects.count()
        self.authorized_client_test_user.get(
            reverse('posts:profile_follow', kwargs={'username': 'TestName'}))
        self.assertEqual(Follow.objects.count(), follows_count + 1)

    def test_follow_delete_correct(self):
        """Авторизованный пользователь может удалять подписки."""
        follows_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': 'Following'}))
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_post_appear_followers(self):
        """Новый пост появляется только у подписчиков."""
        Post.objects.create(
            author=User.objects.get(username='Following'),
            text='Тестовый текст ленты',
        )
        follower = User.objects.get(username='Follower')
        authorized_client_follower = Client()
        authorized_client_follower.force_login(follower)
        response = authorized_client_follower.get(
            reverse('posts:follow_index'))
        posts_count_follow = len(response.context['page_obj'])
        response = self.authorized_client_author.get(
            reverse('posts:follow_index'))
        posts_count_not_follow = len(response.context['page_obj'])
        Post.objects.create(
            author=User.objects.get(username='Following'),
            text='Тестовый текст ленты 2',
        )
        response = authorized_client_follower.get(
            reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']), posts_count_follow + 1)
        response = self.authorized_client_author.get(
            reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']), posts_count_not_follow)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        num_page = 14
        author = User.objects.create_user(username='TestName')
        group = Group.objects.create(title='TestGroup_1',
                                           slug='TestGroup_1')
        for i in range(num_page):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=author,
                group=group
            )

    def setUp(self):
        cache.clear()
        self.user = User.objects.get(username='TestName')
        self.guest_client = Client()
        self.templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'TestGroup_1'}),
            reverse('posts:profile', kwargs={'username': 'TestName'})
        ]

    def page_records_number(self, page_number):
        for address in self.templates_pages_names:
            with self.subTest(address=address):
                response = self.client.get(f'{address}?page={page_number}')
                rec_number = len(response.context['page_obj'])
        return rec_number

    def test_first_page_contains_ten_records(self):
        """Количество постов на первых страницах равно 10."""
        rec_number = self.page_records_number(1)
        self.assertEqual(rec_number, 10)

    def test_second_page_contains_three_records(self):
        """На вторых страницах должно быть четыре поста."""
        rec_number = self.page_records_number(2)
        self.assertEqual(rec_number, 4)

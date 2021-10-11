from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='Заголовок группы',
            slug='test_slug',
            description='Описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Guest')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.create_user(username='not_author')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

        self.post = Post.objects.create(
            author=self.user,
            text='текст тестового поста'
        )

    def test_urls_unexisting_page(self):
        response = self.guest_client.get('/pararam/')
        self.assertEqual(response.status_code, 404, 'error')

    def test_urls_uses_correct_template_guest(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test_slug/',
            'posts/profile.html': '/profile/Guest/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
            'users/login.html': '/auth/login/',
            'users/logged_out.html': '/auth/logout/',
            'users/signup.html': '/auth/signup/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template, 'error')

    def test_urls_status_code_guest(self):
        urls_status_code = {
            '/',
            '/group/test_slug/',
            '/profile/Guest/',
            f'/posts/{self.post.pk}/',
            '/about/author/',
            '/about/tech/',
            '/auth/login/',
            '/auth/logout/',
            '/auth/signup/',

        }
        for adress in urls_status_code:
            response = self.guest_client.get(adress)
            self.assertEqual(200, response.status_code, 'error')

    def test_urls_status_code_guest_redirect(self):
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_status_create_auth(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200, 'error')

    def test_urls_status_edit_author(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, 200, 'error')

    def test_urls_status_edit_not_author(self):
        response = self.authorized_client2.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

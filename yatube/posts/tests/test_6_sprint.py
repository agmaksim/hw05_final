import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class Test6(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='username1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user1)
        cls.user2 = User.objects.create_user(username='username2')
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='Группа',
            slug='1',
            description='Описание'
        )
        cls.group2 = Group.objects.create(
            title='Группа2',
            slug='2',
            description='Описание2'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user1,
            group=cls.group,
            image=cls.uploaded
        )

    def test_gif_in_context(self):
        pages = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': Test6.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': Test6.user1.username
            })
        ]
        for reverse_name in pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(
                    Test6.post, response.context['page_obj']
                )
        post_in_page = response.context['page_obj'][0]
        test_var = {
            post_in_page.text: Test6.post.text,
            post_in_page.group: Test6.group,
            post_in_page.author: Test6.user1,
            post_in_page.image.name: 'posts/small.gif',
        }
        for var, res in test_var.items():
            with self.subTest(res=res):
                self.assertEqual(var, res)

    def test_create_post_go_bd(self):
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test text',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': Test6.user1.username
                            }))
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_cache(self):
        self.assertEqual(Post.objects.count(), 1)
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        Post.objects.all().delete()
        post_in_cache = response.context['page_obj'][0]
        self.assertEqual(post_in_cache.text, Test6.post.text)
        cache.clear()
        self.assertEqual(Post.objects.count(), 0)

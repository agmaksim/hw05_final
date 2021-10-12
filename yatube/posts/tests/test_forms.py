import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Follow

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
class TestContextImage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='username1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user1)
        cls.guest_client = Client()
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

    def test_context(self):
        pages = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': TestContextImage.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': TestContextImage.user1.username
            })
        ]
        for reverse_name in pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(
                    TestContextImage.post, response.context['page_obj']
                )
        post_in_page = response.context['page_obj'][0]
        test_var = {
            post_in_page.text: TestContextImage.post.text,
            post_in_page.group: TestContextImage.group,
            post_in_page.author: TestContextImage.user1,
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
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': TestContextImage.user1.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_cache(self):
        self.assertEqual(Post.objects.count(), 1)
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        Post.objects.all().delete()
        post_in_cache = response.context['page_obj'][0]
        self.assertEqual(post_in_cache.text, TestContextImage.post.text)
        cache.clear()
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_guest(self):
        posts_count = Post.objects.count()
        response = self.guest_client.post(reverse('posts:post_create'))
        response_create = (
            reverse('users:login') + '?next='
            + (reverse('posts:post_create')))
        self.assertRedirects(response, response_create)
        self.assertEqual(posts_count, Post.objects.count())

    def test_edit_post(self):
        post_before_edit = self.post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'new text',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': post_before_edit.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_before_edit.pk}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        post_after_edit = Post.objects.filter(text=form_data['text']).first()
        test_var = {
            post_after_edit.text: 'new text',
            post_after_edit.group: self.group,
            post_after_edit.author: self.user1
        }
        for var, res in test_var.items():
            with self.subTest(res=res):
                self.assertEqual(var, res)

    def test_follow(self):
        follow_count = Follow.objects.count()
        follow_url = reverse(
            'posts:profile_follow', kwargs={
                'username': TestContextImage.user1.username
            })
        self.authorized_client2.get(follow_url)
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow(self):
        follow_url = reverse(
            'posts:profile_follow', kwargs={
                'username': TestContextImage.user1.username
            })
        unfollow_url = reverse(
            'posts:profile_unfollow', kwargs={
                'username': TestContextImage.user1.username
            })
        self.authorized_client2.get(follow_url)
        follow_count = Follow.objects.count()
        self.authorized_client2.get(unfollow_url)
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_context(self):
        follow_url = reverse(
            'posts:profile_follow', kwargs={
                'username': TestContextImage.user1.username
            })
        follow_index_url = reverse(
            'posts:follow_index'
            )
        self.authorized_client2.get(follow_url)
        author_response = self.authorized_client.get(
            follow_index_url
            ).context['page_obj']
        self.assertNotIn(self.post, author_response)
        not_author_response = self.authorized_client2.get(
            follow_index_url
            ).context['page_obj']
        self.assertIn(self.post, not_author_response)

    def test_comment_login(self):
        self.post.comments.all().delete()
        form_data = {
            'text': 'COMMENT'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={
                    'post_id': self.post.pk
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.comments.count(), 1)
        comment = self.post.comments.all()[0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user1)
        self.assertEqual(comment.post, self.post)

    def test_comment_guest(self):
        self.post.comments.all().delete()
        form_data = {
            'text': 'COMMENT'
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment', kwargs={
                    'post_id': self.post.pk
                    }),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.comments.count(), 0)

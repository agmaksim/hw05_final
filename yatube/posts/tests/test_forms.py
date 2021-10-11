from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user1')
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.guest_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='old text',
        )
        self.group = Group.objects.create(
            title='Group name',
            slug='test_slug',
            description='тестовое описание',
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.pk,
            'text': 'create text'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostCreateFormTests.user.username
            })
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        create_post = Post.objects.filter(text=form_data['text']).first()
        test_var = {
            create_post.text: form_data['text'],
            create_post.group: self.group,
            create_post.author: self.user
        }
        for var, res in test_var.items():
            with self.subTest(res=res):
                self.assertEqual(var, res)

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
            post_after_edit.author: self.user
        }
        for var, res in test_var.items():
            with self.subTest(res=res):
                self.assertEqual(var, res)

    def test_create_post_guest(self):
        posts_count = Post.objects.count()
        response = self.guest_client.post(reverse('posts:post_create'))
        response_create = (
            reverse('users:login') + '?next='
            + (reverse('posts:post_create')))
        self.assertRedirects(response, response_create)
        self.assertEqual(posts_count, Post.objects.count())

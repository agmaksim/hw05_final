from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Описание'
        )
        cls.user = User.objects.create_user(username='user1')
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='test text',
            group=cls.group
        )
        for post in range(8):
            Post.objects.create(
                author=cls.user,
                text='test text',
                group=PostPagesTests.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='test text',
            group=self.group
        )
        self.group2 = Group.objects.create(
            title='test_group2',
            slug='test_slug2',
            description='Описание'
        )

    def test_urls_uses_correct_template_reverse(self):
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={
                    'slug': PostPagesTests.group.slug
                }):
            'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={
                    'username': PostPagesTests.user.username
                }):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={
                    'post_id': self.post.pk}):
                    'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:signup'): 'users/signup.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_first_page_contains_ten_records(self):
        reverse_dict_for_paginator_test = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': PostPagesTests.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username
            }),
        ]
        for name_url in reverse_dict_for_paginator_test:
            with self.subTest(name_url=name_url):
                response = self.authorized_client.get(name_url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_context_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        for post in response.context['page_obj']:
            self.assertIsInstance(post, Post)

    def test_context_group_list(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts', kwargs={
                    'slug': PostPagesTests.group.slug
                }))
        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.group)

    def test_context_profile(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username
            }))
        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.user)

    def test_context_post_detail(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post.pk}))
        test_pk = response.context['post'].pk
        self.assertEqual(test_pk, self.post.pk)

    def test_context_post_create(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_one_post_in_page(self):
        expected_pages = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                'slug': PostPagesTests.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username
            })
        ]
        for reverse_name in expected_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(
                    PostPagesTests.post1, response.context['page_obj']
                )
        post_in_page = response.context['page_obj'][0]
        test_var = {
            post_in_page.text: PostPagesTests.post1.text,
            post_in_page.group: PostPagesTests.group,
            post_in_page.author: PostPagesTests.user,
        }
        for var, res in test_var.items():
            with self.subTest(res=res):
                self.assertEqual(var, res)

    def test_one_post_not_in_group(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group2.slug}),)
        self.assertNotIn(
            PostPagesTests.post1, response.context['page_obj']
        )

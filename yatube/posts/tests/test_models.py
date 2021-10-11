from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Group name',
            slug='test_slug',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='123456789101112test',
        )

    def test_15_group_verbose_help(self):
        dict_for_test = {
            '123456789101112': PostModelTest.post.text[:15],
            'Group name': PostModelTest.group.title,
            'Содержание': PostModelTest.post._meta.get_field(
                'text').verbose_name,
            'Содержание поста': PostModelTest.post._meta.get_field(
                'text').help_text
        }
        for act, result in dict_for_test.items():
            with self.subTest(result=result):
                self.assertEqual(act, result)

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from branches.models import Branch, BranchComment

User = get_user_model()

class BranchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='branch_user',
            password='branch-pass',
            first_name='Филиал',
            last_name='Пользователь',
        )
        self.branch = Branch.objects.create(
            name='Филиал Тест',
            description='Тестовый филиал.',
            address='ул. Тестовая, 10',
            phone='+7 701 111 22 33',
            schedule='пн-пт 06:00-22:00',
            photo=SimpleUploadedFile('b.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            is_active=True,
        )

    def test_branch_detail_page(self):
        response = self.client.get(reverse('branch_detail', kwargs={'pk': self.branch.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый филиал.')

    def test_branch_cabinet_page(self):
        self.client.login(username='branch_user', password='branch-pass')
        response = self.client.get(reverse('branch_cabinet', kwargs={'pk': self.branch.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.branch.name)
        self.assertIn('branch', response.context)
        self.assertIn('competitions_count', response.context)
        self.assertIn('athletes_count', response.context)
        self.assertIn('trainers_count', response.context)

    def test_branch_comment_ajax(self):
        self.client.login(username='branch_user', password='branch-pass')
        response = self.client.post(reverse('branch_add_comment', kwargs={'pk': self.branch.pk}), {'text': 'Отличный бассейн'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True, 'user': self.user.get_full_name(), 'text': 'Отличный бассейн', 'date': self.branch.comments.first().created_at.strftime('%d.%m.%Y %H:%M'), 'total': 1})

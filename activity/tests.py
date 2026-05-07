from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from activity.models import Activity

User = get_user_model()

class ActivityFeedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='activity_user',
            email='activity@test.local',
            password='testpass',
            first_name='Активный',
            last_name='Пользователь'
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@test.local',
            password='testpass',
            first_name='Другой',
            last_name='Пользователь'
        )
        Activity.objects.create(
            user=self.user,
            activity_type='achievement',
            title='Новое достижение',
            description='Показал лучший результат',
            link='/competitions/1/'
        )
        Activity.objects.create(
            user=self.other_user,
            activity_type='competition',
            title='Скоро старт',
            description='Регистрация открыта',
            link='/competitions/2/'
        )

    def test_global_activity_feed_shows_all_entries(self):
        response = self.client.get(reverse('activity_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Лента активности')
        self.assertContains(response, 'Новое достижение')
        self.assertContains(response, 'Скоро старт')

    def test_activity_feed_filter_by_type(self):
        response = self.client.get(reverse('activity_list') + '?type=achievement')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новое достижение')
        self.assertNotContains(response, 'Скоро старт')

    def test_personal_activity_feed_requires_login(self):
        response = self.client.get(reverse('activity_personal_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_personal_activity_feed_shows_only_user_entries(self):
        self.client.login(username='activity_user', password='testpass')
        response = self.client.get(reverse('activity_personal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новое достижение')
        self.assertNotContains(response, 'Скоро старт')
        self.assertContains(response, 'Моя лента активности')

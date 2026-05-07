from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from users.auth import assign_user_to_role
from users.models import AthleteProfile, FanProfile, Achievement
from trainers.models import Trainer
from branches.models import Branch
from competitions.models import Competition, Discipline, Registration

User = get_user_model()

class UserProfileTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='Trainer')
        Group.objects.get_or_create(name='Athlete')
        Group.objects.get_or_create(name='Fan')

        self.trainer_user = User.objects.create_user(
            username='trainer_test',
            email='trainer@test.local',
            password='trainer-pass',
            first_name='Тренер',
            last_name='Тест'
        )
        assign_user_to_role(self.trainer_user, 'trainer')
        photo = SimpleUploadedFile('trainer.png', b'\x89PNG\r\n\x1a\n', content_type='image/png')
        self.trainer = Trainer.objects.create(
            user=self.trainer_user,
            bio='Тренер по выработке техники.',
            experience_years=5,
            specialization='Вольный стиль',
            photo=photo,
            certifications='Сертификат ФИНА',
            programs='Персональные тренировки',
            schedule='пн-пт 18:00-20:00',
            whatsapp_url='https://wa.me/77010000000',
            instagram_url='https://instagram.com/trainer_test',
            rating=4.7,
        )

        self.branch = Branch.objects.create(
            name='Филиал i.SWiM',
            description='Главный филиал школы.',
            address='ул. Примерная, 1',
            phone='+7 701 000 00 00',
            schedule='пн-пт 06:00-22:00',
            photo=SimpleUploadedFile('branch.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            social_links={'instagram': 'https://instagram.com/iswim_kz'},
            is_active=True,
        )

        self.athlete_user = User.objects.create_user(
            username='athlete_test',
            email='athlete@test.local',
            password='athlete-pass',
            first_name='Спортсмен',
            last_name='Тест'
        )
        assign_user_to_role(self.athlete_user, 'athlete')
        self.athlete_profile = AthleteProfile.objects.create(
            user=self.athlete_user,
            birth_date=date(2010, 5, 12),
            swimming_level='advanced',
            gender='F',
            instagram_url='https://instagram.com/athlete_test',
            experience_years=6,
        )

        self.fan_user = User.objects.create_user(
            username='fan_test',
            email='fan@test.local',
            password='fan-pass',
            first_name='Болельщик',
            last_name='Тест'
        )
        assign_user_to_role(self.fan_user, 'fan')
        self.fan_profile = FanProfile.objects.create(user=self.fan_user)
        self.fan_profile.favorite_athletes.add(self.athlete_profile)

        self.competition = Competition.objects.create(
            title='Кубок теста',
            description='Внутренний старт.',
            location='Бассейн №1',
            branch=self.branch,
            start_date=date.today(),
            status='upcoming',
            lanes=6,
            created_by=self.trainer_user,
        )
        self.discipline = Discipline.objects.create(
            competition=self.competition,
            style='free',
            distance=100,
        )
        self.registration = Registration.objects.create(
            competition=self.competition,
            athlete=self.athlete_profile,
            discipline=self.discipline,
            coach=self.trainer_user,
            branch=self.branch,
            preliminary_time='1:20.00',
            is_confirmed=True,
        )
        Achievement.objects.create(
            athlete=self.athlete_profile,
            title='Золото теста',
            achievement_type='medal',
            competition='Кубок теста',
            date=date.today(),
        )

    def test_athlete_profile_requires_login(self):
        response = self.client.get(reverse('athlete_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_fan_profile_requires_login(self):
        response = self.client.get(reverse('fan_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_trainer_profile_requires_login(self):
        response = self.client.get(reverse('trainer_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_trainer_profile_page(self):
        self.client.login(username='trainer_test', password='trainer-pass')
        response = self.client.get(reverse('trainer_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тренер по выработке техники.')
        self.assertContains(response, 'WhatsApp')
        self.assertContains(response, 'Instagram')
        self.assertIn('trainer', response.context)
        self.assertIn('students', response.context)
        self.assertIn('upcoming_competitions', response.context)
        self.assertIn('branches', response.context)

    def test_athlete_profile_page(self):
        self.client.login(username='athlete_test', password='athlete-pass')
        response = self.client.get(reverse('athlete_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спортсмен Тест')
        self.assertContains(response, 'Продвинутый')
        self.assertContains(response, 'Мои достижения')
        self.assertIn('profile', response.context)
        self.assertIn('achievements', response.context)
        self.assertIn('current_coach', response.context)
        self.assertIn('current_branch', response.context)

    def test_fan_profile_page(self):
        self.client.login(username='fan_test', password='fan-pass')
        response = self.client.get(reverse('fan_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Персональный кабинет болельщика')
        self.assertContains(response, 'Спортсмен Тест')
        self.assertIn('favorite_athletes', response.context)
        self.assertIn('favorite_count', response.context)
        self.assertIn('upcoming_competitions', response.context)

    def test_public_athlete_page_shows_trainer_and_branch(self):
        response = self.client.get(reverse('public_athlete', kwargs={'username': self.athlete_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тренер:')
        self.assertContains(response, self.trainer_user.get_full_name())
        self.assertContains(response, 'Филиал:')
        self.assertContains(response, self.branch.name)
        self.assertContains(response, 'Стаж')
        self.assertContains(response, '6')

    def test_public_fan_page_shows_favorites(self):
        response = self.client.get(reverse('public_fan', kwargs={'username': self.fan_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.fan_user.get_full_name())
        self.assertContains(response, self.athlete_user.get_full_name())

    def test_profile_redirect_for_roles(self):
        self.client.login(username='trainer_test', password='trainer-pass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('trainer_profile'), response.url)

        self.client.logout()
        self.client.login(username='athlete_test', password='athlete-pass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('athlete_profile'), response.url)

        self.client.logout()
        self.client.login(username='fan_test', password='fan-pass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('fan_profile'), response.url)

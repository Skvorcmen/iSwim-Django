from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from trainers.models import Trainer

User = get_user_model()

class TrainerDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='trainer_public',
            password='secret',
            first_name='Публичный',
            last_name='Тренер',
        )
        self.trainer = Trainer.objects.create(
            user=self.user,
            bio='Публичный профиль тренера.',
            experience_years=3,
            specialization='Брасс',
            photo=SimpleUploadedFile('t.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            certifications='Сертификат',
            programs='Тренировки',
            schedule='пн-пт',
            whatsapp_url='https://wa.me/77019999999',
            instagram_url='https://instagram.com/trainer_public',
            rating=4.2,
        )

    def test_trainer_detail_page(self):
        response = self.client.get(reverse('trainer_detail', kwargs={'pk': self.trainer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Публичный профиль тренера.')
        self.assertContains(response, 'Брасс')
        self.assertContains(response, 'Instagram')

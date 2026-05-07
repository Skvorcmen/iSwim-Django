from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from openpyxl import Workbook

from activity.models import Activity
from branches.models import Branch
from competitions.models import (
    AgeCategory,
    Competition,
    Discipline,
    Heat,
    HeatAssignment,
    Registration,
)
from users.models import Achievement, AthleteProfile, SecretaryProfile
from trainers.models import Trainer


class CompetitionsFlowTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.secretary = self.user_model.objects.create_user(
            username="sec",
            password="pass12345",
            first_name="Sec",
            last_name="Retary",
        )
        SecretaryProfile.objects.create(user=self.secretary)

        self.branch = Branch.objects.create(
            name="Central",
            address="Main street",
            phone="+70000000000",
            schedule="09:00-18:00",
            photo="branches/test.jpg",
        )
        self.competition = Competition.objects.create(
            title="Spring Cup",
            location="Pool Arena",
            start_date=date(2026, 5, 1),
            status="ongoing",
            lanes=6,
            created_by=self.secretary,
            branch=self.branch,
        )
        self.category = AgeCategory.objects.create(
            competition=self.competition,
            name="2010 boys",
            birth_year_from=2010,
            birth_year_to=2010,
            gender="M",
        )
        self.discipline = Discipline.objects.create(
            competition=self.competition,
            style="free",
            distance=50,
        )
        self.heat = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=self.category,
            number=1,
        )

    def _create_assignment(self, username, first_name, lane, result_time):
        user = self.user_model.objects.create_user(
            username=username,
            password="pass12345",
            first_name=first_name,
            last_name="Swimmer",
        )
        athlete = AthleteProfile.objects.create(
            user=user,
            birth_date=date(2010, 1, 1),
            gender="M",
        )
        reg = Registration.objects.create(
            competition=self.competition,
            athlete=athlete,
            discipline=self.discipline,
            coach=self.secretary,
            branch=self.branch,
        )
        return HeatAssignment.objects.create(
            heat=self.heat,
            registration=reg,
            lane=lane,
            result_time=result_time,
        )

    def test_registered_athletes_search_returns_results(self):
        self._create_assignment("ivanov", "Ivan", 1, "")
        self.client.force_login(self.secretary)

        response = self.client.get(
            reverse("registered_athletes", kwargs={"pk": self.competition.pk}),
            {"q": "iva"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 1)
        self.assertIn("Ivan", data[0]["name"])

    def test_finalize_results_assigns_places_with_ties(self):
        a1 = self._create_assignment("swim1", "Alex", 1, "00:28.50")
        a2 = self._create_assignment("swim2", "Boris", 2, "00:28.50")
        a3 = self._create_assignment("swim3", "Cyril", 3, "00:29.10")
        self.client.force_login(self.secretary)

        response = self.client.get(
            reverse(
                "finalize_results",
                kwargs={
                    "pk": self.competition.pk,
                    "discipline_id": self.discipline.pk,
                    "category_id": self.category.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 302)
        a1.refresh_from_db()
        a2.refresh_from_db()
        a3.refresh_from_db()
        self.assertEqual(a1.place, 1)
        self.assertEqual(a2.place, 1)
        self.assertEqual(a3.place, 3)

    def test_competition_protocol_contains_finalized_results(self):
        self._create_assignment("proto1", "Proto", 1, "00:28.10")
        self.client.force_login(self.secretary)
        self.client.get(
            reverse(
                "finalize_results",
                kwargs={
                    "pk": self.competition.pk,
                    "discipline_id": self.discipline.pk,
                    "category_id": self.category.pk,
                },
            )
        )
        response = self.client.get(reverse("competition_protocol", kwargs={"pk": self.competition.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Протокол соревнований")
        self.assertContains(response, "Proto")
        csv_response = self.client.get(reverse("competition_protocol_csv", kwargs={"pk": self.competition.pk}))
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response["Content-Type"])
        csv_text = csv_response.content.decode("utf-8-sig")
        self.assertIn("competition_title", csv_text)
        self.assertIn("Proto", csv_text)

    def test_finalize_results_requires_valid_times(self):
        self._create_assignment("notime1", "No", 5, "")
        self.client.force_login(self.secretary)
        response = self.client.get(
            reverse(
                "finalize_results",
                kwargs={
                    "pk": self.competition.pk,
                    "discipline_id": self.discipline.pk,
                    "category_id": self.category.pk,
                },
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            HeatAssignment.objects.filter(
                heat__competition=self.competition,
                heat__discipline=self.discipline,
                heat__age_category=self.category,
                place__isnull=False,
            ).exists()
        )

    def test_finish_competition_is_idempotent(self):
        assign = self._create_assignment("medal1", "Daniil", 1, "00:27.90")
        assign.place = 1
        assign.save()
        self.client.force_login(self.secretary)

        url = reverse("finish_competition", kwargs={"pk": self.competition.pk})
        first = self.client.get(url)
        second = self.client.get(url)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.status, "finished")
        self.assertEqual(Achievement.objects.filter(achievement_type="medal").count(), 1)
        self.assertEqual(Achievement.objects.filter(achievement_type="record").count(), 1)
        self.assertEqual(Activity.objects.filter(activity_type="competition").count(), 1)

    def test_finish_competition_blocked_when_not_all_disciplines_finalized(self):
        self._create_assignment("unfinished1", "Un", 6, "00:32.20")
        self.client.force_login(self.secretary)
        response = self.client.get(reverse("finish_competition", kwargs={"pk": self.competition.pk}))
        self.assertEqual(response.status_code, 302)
        self.competition.refresh_from_db()
        self.assertNotEqual(self.competition.status, "finished")

    def test_live_competition_sets_ongoing_for_secretary(self):
        self.competition.status = "closed"
        self.competition.save(update_fields=["status"])
        self.client.force_login(self.secretary)
        response = self.client.get(reverse("live_competition", kwargs={"pk": self.competition.pk}))
        self.assertEqual(response.status_code, 200)
        self.competition.refresh_from_db()
        self.assertEqual(self.competition.status, "ongoing")
        self.assertContains(response, "Завершение недоступно")

    def test_competition_detail_shows_disabled_hints(self):
        self.competition.status = "finished"
        self.competition.save(update_fields=["status"])
        self.client.force_login(self.secretary)
        response = self.client.get(reverse("competition_detail", kwargs={"pk": self.competition.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Старт недоступен")
        self.assertContains(response, "Закрытие недоступно")
        self.assertContains(response, "Статусная панель")
        self.assertContains(response, "Прогресс соревнования")

    def test_save_result_rejects_invalid_time_format(self):
        assign = self._create_assignment("badtime", "Bad", 4, "")
        self.client.force_login(self.secretary)
        response = self.client.post(
            reverse("save_result", kwargs={"assignment_id": assign.pk}),
            data='{"time":"28.50"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        assign.refresh_from_db()
        self.assertEqual(assign.result_time, "")

    def test_upload_application_and_generate_heats_flow(self):
        trainer_user = self.user_model.objects.create_user(
            username="trainer1",
            password="pass12345",
            first_name="Train",
            last_name="Er",
        )
        trainer = Trainer.objects.create(
            user=trainer_user,
            bio="Bio",
            experience_years=5,
            specialization="Sprint",
            photo="trainers/test.jpg",
        )
        trainer.branches.add(self.branch)

        wb = Workbook()
        ws = wb.active
        ws.append(["Фамилия", "Имя", "Пол (М/Ж)", "Год рождения", "Стиль", "Дистанция (м)", "Предв. время"])
        ws.append(["Иванов", "Иван", "М", 2010, "Вольный стиль", 50, "00:28,50"])
        ws.append(["Петров", "Петр", "М", 2010, "Вольный стиль", 50, "00:30,10"])
        payload = BytesIO()
        wb.save(payload)
        payload.seek(0)
        upload = SimpleUploadedFile(
            "zayavka.xlsx",
            payload.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        self.client.force_login(trainer_user)
        upload_response = self.client.post(
            reverse("upload_application", kwargs={"pk": self.competition.pk}),
            {"file": upload},
        )
        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(Registration.objects.filter(competition=self.competition).count(), 2)
        self.assertContains(upload_response, "Отчёт импорта")
        self.assertContains(upload_response, "Создано:")

        self.client.force_login(self.secretary)
        gen_response = self.client.get(reverse("generate_heats", kwargs={"pk": self.competition.pk}))
        self.assertEqual(gen_response.status_code, 302)
        heat = (
            Heat.objects.filter(
                competition=self.competition,
                discipline=self.discipline,
                age_category=self.category,
                assignments__isnull=False,
            )
            .distinct()
            .first()
        )
        self.assertIsNotNone(heat)
        self.assertEqual(heat.assignments.count(), 2)

    def test_upload_application_skips_invalid_rows_and_continues(self):
        trainer_user = self.user_model.objects.create_user(
            username="trainer2",
            password="pass12345",
            first_name="Train",
            last_name="Two",
        )
        trainer = Trainer.objects.create(
            user=trainer_user,
            bio="Bio",
            experience_years=4,
            specialization="Backstroke",
            photo="trainers/test2.jpg",
        )
        trainer.branches.add(self.branch)

        wb = Workbook()
        ws = wb.active
        ws.append(["Фамилия", "Имя", "Пол (М/Ж)", "Год рождения", "Стиль", "Дистанция (м)", "Предв. время"])
        ws.append(["", "БезФамилии", "М", 2010, "Вольный стиль", 50, "00:31,00"])  # skipped
        ws.append(["Сидоров", "Сидр", "М", "bad_year", "Вольный стиль", 50, "00:29,00"])  # error
        ws.append(["Орлов", "Олег", "М", 2010, "Вольный стиль", 50, "00:28,20"])  # created
        payload = BytesIO()
        wb.save(payload)
        payload.seek(0)
        upload = SimpleUploadedFile(
            "zayavka_bad.xlsx",
            payload.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        self.client.force_login(trainer_user)
        response = self.client.post(
            reverse("upload_application", kwargs={"pk": self.competition.pk}),
            {"file": upload},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Registration.objects.filter(competition=self.competition).count(), 1)
        self.assertContains(response, "Ошибки:")
        csv_response = self.client.get(
            reverse("download_import_errors_csv", kwargs={"pk": self.competition.pk})
        )
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response["Content-Type"])
        self.assertIn("Строка", csv_response.content.decode("utf-8-sig"))


class CompetitionApiTests(TestCase):
    """Тесты публичного REST API соревнований (Phase 2.5)"""

    def setUp(self):
        self.user_model = get_user_model()
        self.secretary = self.user_model.objects.create_user(
            username="sec_api",
            password="pass12345",
            first_name="Sec",
            last_name="Retary",
        )
        SecretaryProfile.objects.create(user=self.secretary)
        self.branch = Branch.objects.create(
            name="API Branch",
            address="API address",
            phone="+70000000001",
            schedule="09:00-18:00",
        )
        self.competition = Competition.objects.create(
            title="API Cup",
            location="API Pool",
            start_date=date(2026, 6, 1),
            status="ongoing",
            lanes=6,
            created_by=self.secretary,
            branch=self.branch,
        )
        self.category = AgeCategory.objects.create(
            competition=self.competition,
            name="2010 boys",
            birth_year_from=2010,
            birth_year_to=2010,
            gender="M",
        )
        self.discipline = Discipline.objects.create(
            competition=self.competition,
            style="free",
            distance=50,
        )
        self.heat = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=self.category,
            number=1,
        )

    def _create_assignment(self, username, first_name, lane, result_time, place=None):
        user = self.user_model.objects.create_user(
            username=username,
            password="pass12345",
            first_name=first_name,
            last_name="Swimmer",
        )
        athlete = AthleteProfile.objects.create(
            user=user,
            birth_date=date(2010, 1, 1),
            gender="M",
        )
        reg = Registration.objects.create(
            competition=self.competition,
            athlete=athlete,
            discipline=self.discipline,
            coach=self.secretary,
            branch=self.branch,
        )
        assignment = HeatAssignment.objects.create(
            heat=self.heat,
            registration=reg,
            lane=lane,
            result_time=result_time,
        )
        if place is not None:
            assignment.place = place
            assignment.save(update_fields=['place'])
        return assignment

    def test_competition_api_list(self):
        response = self.client.get(reverse('competition_api_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(any(item['id'] == self.competition.pk for item in data))

    def test_competition_api_detail(self):
        response = self.client.get(reverse('competition_api_detail', kwargs={'pk': self.competition.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.competition.pk)
        self.assertEqual(data['title'], 'API Cup')
        self.assertEqual(len(data['disciplines']), 1)
        self.assertEqual(len(data['age_categories']), 1)

    def test_competition_api_results(self):
        self._create_assignment('api1', 'Api', 1, '00:28.50', place=1)
        self._create_assignment('api2', 'Rest', 2, '00:29.70', place=2)
        response = self.client.get(reverse('competition_api_results', kwargs={'pk': self.competition.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['discipline'], str(self.discipline))
        self.assertEqual(data[0]['category'], self.category.name)

    def test_competition_api_heat_assignments(self):
        assignment = self._create_assignment('apiheat', 'Heat', 3, '00:30.80')
        response = self.client.get(reverse('competition_api_heat_assignments', kwargs={'heat_id': self.heat.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['lane'], 3)
        self.assertEqual(data[0]['athlete'], assignment.registration.athlete.user.get_full_name())


# ==================== PHASE 1 TESTS ====================

class ResultTimeValidationTests(TestCase):
    """Тесты валидации формата времени (Phase 1)"""
    
    def test_valid_time_formats(self):
        """Проверяет корректные форматы времени"""
        from competitions.validators import validate_result_time
        from django.core.exceptions import ValidationError
        
        valid_times = [
            '1:23.45',
            '10:45.67',
            '2:03.14',
            '12:34.567',  # 3 цифры после точки
        ]
        for time_str in valid_times:
            try:
                validate_result_time(time_str)
            except ValidationError:
                self.fail(f"validate_result_time raised ValidationError for valid time: {time_str}")
    
    def test_invalid_time_formats(self):
        """Проверяет некорректные форматы времени"""
        from competitions.validators import validate_result_time
        from django.core.exceptions import ValidationError
        
        invalid_times = [
            '123.45',       # без двоеточия
            '1:2.45',       # одна цифра в секундах
            '25:30.00',     # 25 минут
            'abc:de.fg',    # не цифры
        ]
        for time_str in invalid_times:
            with self.assertRaises(ValidationError):
                validate_result_time(time_str)


class NewsGenerationTests(TestCase):
    """Тесты генерации новостей после соревнования (Phase 1)"""
    
    def test_news_created_on_competition_finish(self):
        """Тест создания новостей при завершении соревнования"""
        from news.models import News
        
        secretary = get_user_model().objects.create_user(
            username='sec',
            password='pass'
        )
        SecretaryProfile.objects.create(user=secretary)
        
        branch = Branch.objects.create(name='Test', address='Test', phone='123')
        
        comp = Competition.objects.create(
            title='Test Comp',
            location='Pool',
            start_date=date(2026, 5, 1),
            lanes=6,
            created_by=secretary,
            branch=branch,
            status='ongoing'
        )
        
        # Сначала нет новостей
        self.assertEqual(News.objects.filter(competition=comp).count(), 0)
        
        # Завершаем соревнование
        comp.status = 'finished'
        comp.save()
        
        # Проверяем, что новость была создана
        news = News.objects.filter(competition=comp)
        self.assertEqual(news.count(), 1)
        self.assertIn('результат', news.first().title.lower())


class HeatAssignmentStatusTests(TestCase):
    """Тесты нового поля status в HeatAssignment (Phase 1)"""
    
    def test_heatassignment_status_field_choices(self):
        """Проверяет что status field существует с правильными choices"""
        from competitions.models import HeatAssignment
        
        # Проверяем что choices существуют
        self.assertEqual(len(HeatAssignment.STATUS_CHOICES), 4)
        choices_dict = dict(HeatAssignment.STATUS_CHOICES)
        self.assertIn('finished', choices_dict)
        self.assertIn('dnf', choices_dict)
        self.assertIn('disqualified', choices_dict)
        self.assertIn('false_start', choices_dict)
    
    def test_heatassignment_can_set_dnf_status(self):
        """Проверяет что можно установить DNF статус"""
        secretary = get_user_model().objects.create_user(
            username='sec2',
            password='pass'
        )
        SecretaryProfile.objects.create(user=secretary)
        
        athlete_user = get_user_model().objects.create_user(
            username='athlete',
            password='pass'
        )
        athlete = AthleteProfile.objects.create(
            user=athlete_user,
            birth_date=date(2010, 1, 1)
        )
        
        branch = Branch.objects.create(name='Test', address='Test', phone='123')
        
        comp = Competition.objects.create(
            title='Test',
            location='Pool',
            start_date=date(2026, 5, 1),
            lanes=6,
            created_by=secretary,
            branch=branch
        )
        
        cat = AgeCategory.objects.create(
            competition=comp,
            name='Test Cat',
            birth_year_from=2010,
            birth_year_to=2010,
            gender='M'
        )
        
        disc = Discipline.objects.create(
            competition=comp,
            style='free',
            distance=50
        )
        
        heat = Heat.objects.create(
            competition=comp,
            discipline=disc,
            age_category=cat,
            number=1
        )
        
        reg = Registration.objects.create(
            competition=comp,
            athlete=athlete,
            discipline=disc,
            branch=branch
        )
        
        assign = HeatAssignment.objects.create(
            heat=heat,
            registration=reg,
            lane=1,
            result_time='',
            status='dnf'
        )
        
        self.assertEqual(assign.status, 'dnf')


class RoleBasedAccessTests(TestCase):
    """Тесты системы ролей (Phase 1)"""
    
    def test_get_user_role_function(self):
        """Тест определения роли пользователя"""
        from users.auth import get_user_role
        
        admin = get_user_model().objects.create_superuser('admin', 'a@a.a', 'pass')
        secretary_user = get_user_model().objects.create_user('sec', password='pass')
        SecretaryProfile.objects.create(user=secretary_user)
        
        self.assertEqual(get_user_role(admin), 'admin')
        self.assertEqual(get_user_role(secretary_user), 'secretary')
    
    def test_has_role_function(self):
        """Тест проверки ролей"""
        from users.auth import has_role
        
        secretary_user = get_user_model().objects.create_user('sec3', password='pass')
        SecretaryProfile.objects.create(user=secretary_user)
        
        self.assertTrue(has_role(secretary_user, 'secretary'))
        self.assertFalse(has_role(secretary_user, 'trainer'))


class GroupRoleTests(TestCase):
    """Тесты Django Groups и RoleMiddleware"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user('group_test', password='pass')
        self.group, _ = Group.objects.get_or_create(name='Secretary')

    def test_assign_user_to_role_adds_group(self):
        from users.auth import assign_user_to_role, get_user_role

        assigned = assign_user_to_role(self.user, 'secretary')
        self.assertTrue(assigned)
        self.assertTrue(self.user.groups.filter(name='Secretary').exists())
        self.assertEqual(get_user_role(self.user), 'secretary')

    def test_has_role_checks_group_role(self):
        from users.auth import has_role

        self.user.groups.add(self.group)
        self.assertTrue(has_role(self.user, 'secretary'))
        self.assertFalse(has_role(self.user, 'trainer'))

    def test_role_middleware_populates_user_role(self):
        from users.auth import RoleMiddleware

        self.user.groups.add(self.group)
        request = self.factory.get('/')
        request.user = self.user
        middleware = RoleMiddleware(lambda req: HttpResponse('ok'))
        response = middleware(request)
        self.assertEqual(request.user_role, 'secretary')
        self.assertEqual(response.status_code, 200)


# ==================== PHASE 2 TESTS ====================

class RecordModelTests(TestCase):
    """Тесты для Record model с правильной сегментацией (Phase 2)"""
    
    def setUp(self):
        """Подготовка данных для тестов"""
        self.user_model = get_user_model()
        self.secretary = self.user_model.objects.create_user(
            username='secretary',
            password='pass'
        )
        SecretaryProfile.objects.create(user=self.secretary)
        
        self.athlete_user = self.user_model.objects.create_user(
            username='athlete1',
            password='pass'
        )
        self.athlete = AthleteProfile.objects.create(
            user=self.athlete_user,
            birth_date=date(2010, 1, 1),
            gender='M'
        )
        
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='Test Address',
            phone='+7999999999'
        )
        
        self.competition = Competition.objects.create(
            title='Test Comp',
            location='Pool',
            start_date=date(2026, 5, 1),
            lanes=6,
            created_by=self.secretary,
            branch=self.branch,
            status='ongoing'
        )
        
        self.age_category = AgeCategory.objects.create(
            competition=self.competition,
            name='10-11 Boys',
            birth_year_from=2010,
            birth_year_to=2010,
            gender='M'
        )
        
        self.discipline = Discipline.objects.create(
            competition=self.competition,
            style='free',
            distance=50
        )
        
        self.heat = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=self.age_category,
            number=1
        )
        
        self.registration = Registration.objects.create(
            competition=self.competition,
            athlete=self.athlete,
            discipline=self.discipline,
            branch=self.branch
        )
    
    def test_first_record_creation(self):
        """Тест создания первого рекорда в категории"""
        from competitions.record_services import check_and_update_records
        from competitions.models import Record
        
        # Создаём запись без рекорда
        self.assertEqual(Record.objects.count(), 0)
        
        # Создаём HeatAssignment с результатом
        assignment = HeatAssignment.objects.create(
            heat=self.heat,
            registration=self.registration,
            lane=1,
            result_time='0:28.50',
            status='finished'
        )
        
        # Проверяем рекорд
        record, is_new = check_and_update_records(assignment)
        
        # Проверяем что рекорд был создан
        self.assertIsNotNone(record)
        self.assertTrue(is_new)
        self.assertEqual(Record.objects.count(), 1)
        self.assertEqual(record.time, '0:28.50')
        self.assertTrue(record.is_current)
    
    def test_record_update_faster_time(self):
        """Тест обновления рекорда при более быстром времени"""
        from competitions.record_services import check_and_update_records
        from competitions.models import Record
        
        # Создаём первый рекорд
        assignment1 = HeatAssignment.objects.create(
            heat=self.heat,
            registration=self.registration,
            lane=1,
            result_time='0:28.50',
            status='finished'
        )
        record1, is_new1 = check_and_update_records(assignment1)
        self.assertTrue(is_new1)
        
        # Создаём второй заплыв и регистрацию с более быстрым временем
        heat2 = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=self.age_category,
            number=2
        )
        assignment2 = HeatAssignment.objects.create(
            heat=heat2,
            registration=self.registration,
            lane=1,
            result_time='0:27.30',  # Быстрее
            status='finished'
        )
        record2, is_new2 = check_and_update_records(assignment2)
        
        # Проверяем что новый рекорд был создан
        self.assertIsNotNone(record2)
        self.assertTrue(is_new2)
        
        # Проверяем что старый рекорд помечен как неактуальный
        record1.refresh_from_db()
        self.assertFalse(record1.is_current)
        
        # Проверяем что новый рекорд текущий
        self.assertTrue(record2.is_current)
        self.assertEqual(record2.time, '0:27.30')
        self.assertEqual(Record.objects.count(), 2)
    
    def test_no_record_update_slower_time(self):
        """Тест что более медленное время не обновляет рекорд"""
        from competitions.record_services import check_and_update_records
        from competitions.models import Record
        
        # Создаём первый рекорд
        assignment1 = HeatAssignment.objects.create(
            heat=self.heat,
            registration=self.registration,
            lane=1,
            result_time='0:28.50',
            status='finished'
        )
        record1, is_new1 = check_and_update_records(assignment1)
        self.assertTrue(is_new1)
        
        # Создаём второй заплыв с более медленным временем
        heat2 = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=self.age_category,
            number=2
        )
        assignment2 = HeatAssignment.objects.create(
            heat=heat2,
            registration=self.registration,
            lane=1,
            result_time='0:29.80',  # Медленнее
            status='finished'
        )
        record2, is_new2 = check_and_update_records(assignment2)
        
        # Проверяем что новый рекорд не был создан
        self.assertIsNone(record2)
        self.assertFalse(is_new2)
        
        # Проверяем что всё ещё один рекорд и он текущий
        self.assertEqual(Record.objects.count(), 1)
        record1.refresh_from_db()
        self.assertTrue(record1.is_current)
    
    def test_record_segmentation_by_gender(self):
        """Тест что рекорды правильно сегментированы по полу"""
        from competitions.record_services import check_and_update_records
        from competitions.models import Record
        
        # Создаём мужской рекорд
        assignment_m = HeatAssignment.objects.create(
            heat=self.heat,
            registration=self.registration,
            lane=1,
            result_time='0:28.50',
            status='finished'
        )
        record_m, _ = check_and_update_records(assignment_m)
        
        # Создаём женскую спортсменку
        athlete_f_user = self.user_model.objects.create_user(
            username='athlete_f',
            password='pass'
        )
        athlete_f = AthleteProfile.objects.create(
            user=athlete_f_user,
            birth_date=date(2010, 2, 1),
            gender='F'
        )
        
        # Создаём категорию для женщин
        age_cat_f = AgeCategory.objects.create(
            competition=self.competition,
            name='10-11 Girls',
            birth_year_from=2010,
            birth_year_to=2010,
            gender='F'
        )
        
        # Создаём регистрацию и заплыв для женщины
        reg_f = Registration.objects.create(
            competition=self.competition,
            athlete=athlete_f,
            discipline=self.discipline,
            branch=self.branch
        )
        
        heat_f = Heat.objects.create(
            competition=self.competition,
            discipline=self.discipline,
            age_category=age_cat_f,
            number=3
        )
        
        # Даём женщине более медленное время, чем мужчине
        assignment_f = HeatAssignment.objects.create(
            heat=heat_f,
            registration=reg_f,
            lane=1,
            result_time='0:32.00',  # Медленнее чем мужской рекорд
            status='finished'
        )
        record_f, _ = check_and_update_records(assignment_f)
        
        # Проверяем что оба рекорда существуют (разные по полу)
        self.assertEqual(Record.objects.count(), 2)
        
        # Проверяем что мужской рекорд не изменился
        record_m.refresh_from_db()
        self.assertEqual(record_m.time, '0:28.50')
        
        # Проверяем что женский рекорд независим
        self.assertIsNotNone(record_f)
        self.assertEqual(record_f.time, '0:32.00')
        self.assertEqual(record_f.gender, 'F')
    
    def test_record_not_created_for_dnf(self):
        """Тест что рекорд не создаётся для DNF"""
        from competitions.record_services import check_and_update_records
        from competitions.models import Record
        
        # Создаём DNF запись
        assignment = HeatAssignment.objects.create(
            heat=self.heat,
            registration=self.registration,
            lane=1,
            result_time='0:28.50',
            status='dnf'  # DNF статус
        )
        
        record, is_new = check_and_update_records(assignment)
        
        # Проверяем что рекорд не был создан
        self.assertIsNone(record)
        self.assertFalse(is_new)
        self.assertEqual(Record.objects.count(), 0)

from django.core.management.base import BaseCommand
from competitions.models import HeatAssignment
from athlete_stats.models import AthleteResult, PersonalRecord


def time_to_seconds(time_str):
    if not time_str:
        return 9999.0
    parts = time_str.split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 1:
        return float(parts[0])
    return 9999.0


class Command(BaseCommand):
    help = 'Синхронизирует результаты соревнований в AthleteResult и PersonalRecord'

    def handle(self, *args, **kwargs):
        assignments = HeatAssignment.objects.filter(
            result_time__isnull=False,
            place__isnull=False,
        ).exclude(result_time='').select_related(
            'registration__athlete',
            'registration__athlete__user',
            'heat__discipline',
            'heat__competition',
        )

        created_results = 0
        updated_prs = 0

        for a in assignments:
            athlete = a.registration.athlete
            discipline = a.heat.discipline
            competition = a.heat.competition
            seconds = time_to_seconds(a.result_time)

            result, created = AthleteResult.objects.update_or_create(
                athlete=athlete,
                discipline=discipline,
                competition=competition,
                defaults={
                    'result_time': a.result_time,
                    'result_seconds': seconds,
                    'place': a.place,
                    'date': competition.start_date,
                },
            )
            if created:
                created_results += 1

            pr, created_pr = PersonalRecord.objects.update_or_create(
                athlete=athlete,
                discipline=discipline,
                defaults={
                    'competition': competition,
                    'result_time': a.result_time,
                    'result_seconds': seconds,
                    'date': competition.start_date,
                },
            )
            if created_pr:
                updated_prs += 1
                # Уведомление о новом личном рекорде
                if athlete.user:
                    create_notification(
                        user=athlete.user,
                        notification_type='new_pr',
                        title=f'Новый личный рекорд!',
                        message=f'{athlete.user.get_full_name()} установил новый рекорд в дисциплине {discipline.get_style_display()} {discipline.distance}м: {a.result_time}',
                        link=f'/stats/progress/{athlete.id}/{discipline.id}/'
                    )
            else:
                if seconds < pr.result_seconds:
                    pr.result_time = a.result_time
                    pr.result_seconds = seconds
                    pr.competition = competition
                    pr.date = competition.start_date
                    pr.save()
                    updated_prs += 1
                    # Уведомление об улучшении рекорда
                    if athlete.user:
                        create_notification(
                            user=athlete.user,
                            notification_type='new_pr',
                            title=f'Личный рекорд улучшен!',
                            message=f'{athlete.user.get_full_name()} улучшил результат в дисциплине {discipline.get_style_display()} {discipline.distance}м до {a.result_time}',
                            link=f'/stats/progress/{athlete.id}/{discipline.id}/'
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Синхронизировано: {created_results} результатов, {updated_prs} личных рекордов обновлено'
            )
        )

def create_notification(user, notification_type, title, message, link=''):
    from notifications.models import Notification
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )

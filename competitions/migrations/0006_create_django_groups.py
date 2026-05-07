"""
Migration для создания Django Groups и Permissions.
Запускается автоматически при первой миграции.
"""
from django.db import migrations


def create_groups(apps, schema_editor):
    """Создаёт базовые группы и их permissions."""
    
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Competition = apps.get_model('competitions', 'Competition')
    Heat = apps.get_model('competitions', 'Heat')
    HeatAssignment = apps.get_model('competitions', 'HeatAssignment')
    News = apps.get_model('news', 'News')
    
    comp_ct = ContentType.objects.get_for_model(Competition)
    heat_ct = ContentType.objects.get_for_model(Heat)
    assignment_ct = ContentType.objects.get_for_model(HeatAssignment)
    news_ct = ContentType.objects.get_for_model(News)
    
    # Создаём группы
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    secretary_group, _ = Group.objects.get_or_create(name='Secretary')
    trainer_group, _ = Group.objects.get_or_create(name='Trainer')
    athlete_group, _ = Group.objects.get_or_create(name='Athlete')
    fan_group, _ = Group.objects.get_or_create(name='Fan')
    
    # Admin - полный доступ (всё добавляется через Django admin)
    admin_perms = Permission.objects.filter(
        content_type__in=[comp_ct, heat_ct, assignment_ct, news_ct]
    )
    admin_group.permissions.set(admin_perms)
    
    # Secretary - управление соревнованиями, вводит результаты, финализирует
    secretary_perms = Permission.objects.filter(
        content_type=comp_ct,
        codename__in=['change_competition', 'view_competition']
    ) | Permission.objects.filter(
        content_type=heat_ct,
        codename__in=['change_heat', 'view_heat']
    ) | Permission.objects.filter(
        content_type=assignment_ct,
        codename__in=['change_heatassignment', 'view_heatassignment']
    )
    secretary_group.permissions.set(secretary_perms)
    
    # Trainer - загружает заявки, смотрит результаты
    trainer_perms = Permission.objects.filter(
        content_type__in=[comp_ct, heat_ct, assignment_ct],
        codename__in=['view_competition', 'view_heat', 'view_heatassignment']
    )
    trainer_group.permissions.set(trainer_perms)
    
    # Athlete - смотрит результаты
    athlete_perms = Permission.objects.filter(
        content_type__in=[comp_ct, heat_ct, assignment_ct],
        codename__in=['view_competition', 'view_heat', 'view_heatassignment']
    )
    athlete_group.permissions.set(athlete_perms)
    
    # Fan - только чтение новостей и результатов
    fan_perms = Permission.objects.filter(
        content_type=comp_ct,
        codename='view_competition'
    ) | Permission.objects.filter(
        content_type=news_ct,
        codename='view_news'
    )
    fan_group.permissions.set(fan_perms)


def delete_groups(apps, schema_editor):
    """Удаляет созданные группы при откате миграции."""
    Group = apps.get_model('auth', 'Group')
    
    Group.objects.filter(name__in=['Admin', 'Secretary', 'Trainer', 'Athlete', 'Fan']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0005_alter_heatassignment_result_time_record'),
        ('news', '0003_news_competition_alter_news_image'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]

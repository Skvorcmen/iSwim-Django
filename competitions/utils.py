from users.models import User, AthleteProfile


def get_or_create_athlete(
    first_name: str,
    last_name: str,
    birth_year: int,
    gender: str,
) -> tuple:
    existing = AthleteProfile.objects.filter(
        user__first_name__iexact=first_name,
        user__last_name__iexact=last_name,
        birth_date__year=birth_year,
        gender=gender,
    ).select_related('user').first()

    if existing:
        return existing, False

    base = f'{last_name}_{first_name}_{birth_year}'.lower()
    base = ''.join(c if c.isalnum() or c == '_' else '_' for c in base)

    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}_{counter}'
        counter += 1

    user = User.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=None,
    )

    athlete = AthleteProfile.objects.create(
        user=user,
        birth_date=f'{birth_year}-01-01',
        gender=gender,
    )

    return athlete, True

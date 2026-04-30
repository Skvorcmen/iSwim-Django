from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
import openpyxl, io, json
from openpyxl.worksheet.datavalidation import DataValidation
from .models import Competition, AgeCategory, Discipline, Registration, Heat, HeatAssignment
from users.models import AthleteProfile, User as UserModel
from trainers.models import Trainer

def time_to_seconds(t):
    try:
        t = t.replace(',', '.')
        parts = t.split(':')
        if len(parts) == 2:
            sec_parts = parts[1].split('.')
            return int(parts[0]) * 60 + int(sec_parts[0]) + (int(sec_parts[1]) / 1000 if len(sec_parts) > 1 else 0)
        return float(t)
    except:
        return 999999
from branches.models import Branch

def is_secretary(user):
    return user.is_authenticated and (user.is_staff or hasattr(user, 'secretary_profile'))

def heat_data(request, heat_id):
    heat = get_object_or_404(Heat, id=heat_id)
    assignments = heat.assignments.select_related('registration__athlete__user').order_by('lane')
    data = [{'lane': a.lane, 'name': a.registration.athlete.user.get_full_name(),
             'result_time': a.result_time, 'place': a.place, 
             'id': a.id, 'has_result': bool(a.result_time)} for a in assignments]
    return JsonResponse(data, safe=False)

class CompetitionListView(ListView):
    model = Competition
    template_name = 'competitions/competition_list.html'
    context_object_name = 'competitions'
    queryset = Competition.objects.all().order_by('start_date')

class CompetitionDetailView(DetailView):
    model = Competition
    template_name = 'competitions/competition_detail.html'
    context_object_name = 'comp'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        from .models import check_registration_deadline
        check_registration_deadline(self.object)
        if request.GET.get('close_registration') and is_secretary(request.user):
            self.object.status = 'closed'
            self.object.save()
            messages.success(request, 'Приём заявок закрыт')
            return redirect('competition_detail', pk=self.object.pk)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['disciplines'] = self.object.disciplines.all()
        ctx['age_categories'] = self.object.age_categories.all()
        return ctx

class CompetitionCreateView(LoginRequiredMixin, CreateView):
    model = Competition
    template_name = 'competitions/competition_form.html'
    fields = ['title', 'description', 'location', 'branch', 'start_date', 'end_date',
              'registration_deadline', 'lanes', 'regulation', 'image']
    def get_success_url(self):
        return reverse_lazy('competition_detail', kwargs={'pk': self.object.pk})
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.registration_deadline_time = self.request.POST.get("registration_deadline_time", "23:59")
        response = super().form_valid(form)
        cat_names = self.request.POST.getlist('cat_name')
        cat_from = self.request.POST.getlist('cat_from')
        cat_to = self.request.POST.getlist('cat_to')
        cat_gender = self.request.POST.getlist('cat_gender')
        for i in range(len(cat_names)):
            if cat_names[i].strip():
                AgeCategory.objects.create(
                    competition=self.object, name=cat_names[i],
                    birth_year_from=int(cat_from[i]) if cat_from[i] else 2000,
                    birth_year_to=int(cat_to[i]) if cat_to[i] else 2010,
                    gender=cat_gender[i] if i < len(cat_gender) else 'M')
        styles = self.request.POST.getlist('style')
        distances = self.request.POST.getlist('distance')
        for i in range(len(styles)):
            if distances[i]:
                Discipline.objects.get_or_create(
                    competition=self.object, style=styles[i], distance=int(distances[i]))
                # Создаём запись в ленте активности
        from activity.models import Activity
        Activity.objects.create(
            user=self.request.user,
            activity_type='competition',
            title=f'Создано новое соревнование «{self.object.title}»',
            description=f'{self.object.location} | {self.object.start_date}',
            link=f'/competitions/{self.object.pk}/'
        )
        return response

@login_required
def download_template_excel(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Заявка"
    headers = ['Фамилия', 'Имя', 'Пол (М/Ж)', 'Год рождения', 'Стиль', 'Дистанция (м)', 'Предв. время']
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    example = ['Иванов', 'Иван', 'М', 2010, 'Вольный стиль', 50, '00:28,50']
    for col, v in enumerate(example, 1):
        ws.cell(row=2, column=col, value=v)
    dv1 = DataValidation(type="list", formula1='"Вольный стиль,На спине,Брасс,Баттерфляй,Комплекс"')
    ws.add_data_validation(dv1)
    dv1.add('E2:E500')
    dv2 = DataValidation(type="list", formula1='"М,Ж"')
    ws.add_data_validation(dv2)
    dv2.add('C2:C500')
    for col, w in zip(['A','B','C','D','E','F','G'], [15,15,10,12,18,14,18]):
        ws.column_dimensions[col].width = w
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=zayavka_{comp.title.replace(" ", "_")}.xlsx'
    return response

@login_required
def upload_application(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        coach = request.user
        branch = request.user.trainer_profile.branches.first() if hasattr(request.user, 'trainer_profile') else None
        style_map = {'вольный стиль': 'free', 'на спине': 'back', 'брасс': 'breast',
                     'баттерфляй': 'fly', 'комплекс': 'medley'}
        created, duplicates = 0, 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0] or not row[1]:
                continue
            last_name, first_name, gender, birth_year, style, distance, time = row[0], row[1], row[2], row[3], row[4], row[5], row[6] or ''
            user, _ = UserModel.objects.get_or_create(
                first_name=first_name, last_name=last_name,
                defaults={'username': f'{last_name}_{first_name}_{birth_year}'.lower()})
            athlete, _ = AthleteProfile.objects.get_or_create(
                user=user, defaults={'birth_date': f'{int(birth_year)}-01-01', 'gender': 'M' if str(gender).upper() in ['M', 'М'] else 'F'})
            athlete.gender = 'M' if str(gender).upper() in ['M', 'М'] else 'F'
            athlete.save()
            style_code = style_map.get(str(style).lower(), 'free')
            try:
                distance_int = int(distance)
            except:
                distance_int = 50
            discipline = Discipline.objects.filter(competition=comp, style=style_code, distance=distance_int).first()
            if not discipline:
                discipline, _ = Discipline.objects.get_or_create(competition=comp, style=style_code, distance=distance_int)
            _, is_new = Registration.objects.get_or_create(
                competition=comp, athlete=athlete, discipline=discipline,
                defaults={'preliminary_time': str(time), 'coach': coach, 'branch': branch})
            if is_new:
                created += 1
            else:
                duplicates += 1
        messages.success(request, f'Загружено: {created} спортсменов. Дубликатов: {duplicates}.')
        return redirect('public_results', pk=pk)
    return render(request, 'competitions/upload_application.html', {'comp': comp})

@user_passes_test(is_secretary)
def manual_register(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        gender = request.POST.get('gender', 'M')
        birth_year = request.POST.get('birth_year', '2010')
        style = request.POST.get('style', 'free')
        distance = request.POST.get('distance', '50')
        time = request.POST.get('time', '')
        coach_id = request.POST.get('coach_id')
        branch_id = request.POST.get('branch_id')
        if not first_name or not last_name:
            messages.error(request, 'Введите имя и фамилию')
            return redirect('manual_register', pk=pk)
        user, _ = UserModel.objects.get_or_create(
            first_name=first_name, last_name=last_name,
            defaults={'username': f'{last_name}_{first_name}_{birth_year}'.lower()})
        athlete, _ = AthleteProfile.objects.get_or_create(
            user=user, defaults={'birth_date': f'{int(birth_year)}-01-01', 'gender': gender})
        athlete.gender = gender
        athlete.save()
        discipline = Discipline.objects.filter(competition=comp, style=style, distance=int(distance)).first()
        if not discipline:
            discipline, _ = Discipline.objects.get_or_create(competition=comp, style=style, distance=int(distance))
        coach = UserModel.objects.get(id=coach_id) if coach_id else request.user
        branch = Branch.objects.get(id=branch_id) if branch_id else None
        reg, created = Registration.objects.get_or_create(
            competition=comp, athlete=athlete, discipline=discipline,
            defaults={'preliminary_time': time, 'coach': coach, 'branch': branch})
        if created:
            messages.success(request, f'{first_name} {last_name} добавлен в заявки')
        else:
            messages.warning(request, 'Спортсмен уже зарегистрирован на эту дисциплину')
        return redirect('public_results', pk=pk)
    coaches = Trainer.objects.all()
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'competitions/manual_register.html', {'comp': comp, 'coaches': coaches, 'branches': branches})

@user_passes_test(is_secretary)
def generate_heats(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    comp.heats.filter(assignments__result_time='').delete()
    for discipline in comp.disciplines.all():
        for age_cat in comp.age_categories.all():
            regs = Registration.objects.filter(
                competition=comp, discipline=discipline,
                athlete__birth_date__year__gte=age_cat.birth_year_from,
                athlete__birth_date__year__lte=age_cat.birth_year_to,
                athlete__gender=age_cat.gender).order_by('preliminary_time')
            if not regs.exists():
                continue
            reg_list = list(regs)
            lanes = comp.lanes
            heats_needed = (len(reg_list) + lanes - 1) // lanes
            for h in range(heats_needed):
                heat = Heat.objects.create(competition=comp, discipline=discipline,
                                           age_category=age_cat, number=h + 1)
                start = h * lanes
                heat_regs = reg_list[start:start + lanes]
                mid = lanes // 2
                left, right = mid - 1, mid
                lane_order = []
                while left >= 0 or right < lanes:
                    if left >= 0:
                        lane_order.append(left)
                        left -= 1
                    if right < lanes:
                        lane_order.append(right)
                        right += 1
                for i, reg in enumerate(heat_regs):
                    if i < len(lane_order):
                        HeatAssignment.objects.create(heat=heat, registration=reg, lane=lane_order[i] + 1)
    messages.success(request, 'Заплывы сформированы!')
    return redirect('public_results', pk=pk)


def get_grouped_heats(comp):
    heats = comp.heats.all().order_by(
        'age_category__birth_year_from', 'age_category__gender',
        'discipline__style', 'discipline__distance', 'number'
    )
    groups = []
    current_key = None
    for h in heats:
        key = (h.age_category.id, h.discipline.id)
        if key != current_key:
            current_key = key
            has_places = HeatAssignment.objects.filter(
                heat__competition=comp,
                heat__discipline=h.discipline,
                heat__age_category=h.age_category,
                place__isnull=False
            ).exists()
            groups.append({
                'category': h.age_category,
                'discipline': h.discipline,
                'comp': comp,
                'heats': [],
                'is_finished': has_places
            })
        groups[-1]['heats'].append(h)
    return groups

@user_passes_test(is_secretary)
def manage_heats(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    groups = get_grouped_heats(comp)
    return render(request, 'competitions/manage_heats.html', {'comp': comp, 'groups': groups})

@user_passes_test(is_secretary)
def available_athletes(request, heat_id):
    heat = get_object_or_404(Heat, id=heat_id)
    assigned_ids = heat.assignments.values_list('registration__athlete_id', flat=True)
    registrations = Registration.objects.filter(
        competition=heat.competition, discipline=heat.discipline,
        athlete__birth_date__year__gte=heat.age_category.birth_year_from,
        athlete__birth_date__year__lte=heat.age_category.birth_year_to,
        athlete__gender=heat.age_category.gender,
    ).exclude(athlete_id__in=assigned_ids).select_related('athlete__user')
    data = [{'id': r.athlete.id, 'name': r.athlete.user.get_full_name()} for r in registrations]
    return JsonResponse(data, safe=False)

@user_passes_test(is_secretary)
def add_to_heat(request, heat_id):
    if request.method == 'POST':
        heat = get_object_or_404(Heat, id=heat_id)
        athlete_id = request.POST.get('athlete_id')
        lane = request.POST.get('lane')
        athlete = get_object_or_404(AthleteProfile, id=athlete_id)
        registration = Registration.objects.filter(
            competition=heat.competition, athlete=athlete, discipline=heat.discipline).first()
        if registration:
            HeatAssignment.objects.create(heat=heat, registration=registration, lane=int(lane))
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

class LiveCompetitionView(LoginRequiredMixin, TemplateView):
    template_name = 'competitions/live_competition.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comp'] = get_object_or_404(Competition, pk=self.kwargs['pk'])
        ctx['groups'] = get_grouped_heats(ctx['comp'])  # ('age_category__birth_year_from', 'age_category__gender', 'discipline__style', 'discipline__distance', 'number')
        ctx["all_disciplines_done"] = all(g["is_finished"] for g in ctx["groups"])
        return ctx

@user_passes_test(is_secretary)
def save_result(request, assignment_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        assignment = get_object_or_404(HeatAssignment, id=assignment_id)
        assignment.result_time = data.get('time', '')
        assignment.save()
        heat = assignment.heat
        # Берём ВСЕ назначения из всех заплывов этой же дисциплины и возрастной категории
        all_assignments = HeatAssignment.objects.filter(
            heat__competition=heat.competition,
            heat__discipline=heat.discipline,
            heat__age_category=heat.age_category,
        ).exclude(result_time='')
        # Места не присваиваем — ждём финализации
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

class PublicResultsView(DetailView):
    model = Competition
    template_name = 'competitions/public_results.html'
    context_object_name = 'comp'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        heats = self.object.heats.all().order_by('age_category__birth_year_from', 'age_category__gender', 'discipline__style', 'discipline__distance', 'number')
        ctx['heats'] = heats
        return ctx

@user_passes_test(is_secretary)
def finalize_results(request, pk, discipline_id, category_id):
    comp = get_object_or_404(Competition, pk=pk)
    all_assignments = HeatAssignment.objects.filter(
        heat__competition=comp,
        heat__discipline_id=discipline_id,
        heat__age_category_id=category_id,
    ).exclude(result_time='')
    
    all_list = list(all_assignments)
    all_list.sort(key=lambda a: time_to_seconds(a.result_time))
    current_place = 1
    prev_time = None
    for i, a in enumerate(all_list):
        t = time_to_seconds(a.result_time)
        if prev_time is not None and t > prev_time:
            current_place = i + 1
        a.place = current_place
        a.save()
        prev_time = t
    
    # Отмечаем незавершивших как DQ
    dnf = HeatAssignment.objects.filter(
        heat__competition=comp,
        heat__discipline_id=discipline_id,
        heat__age_category_id=category_id,
        result_time=''
    )
    dnf.update(place=None)
    
    messages.success(request, '✅ Дисциплина завершена! Места распределены. Результаты доступны на странице просмотра.')
    return redirect('public_results', pk=pk)

@user_passes_test(is_secretary)
def reorder_heats(request, pk):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        for item in data:
            Heat.objects.filter(id=item['id']).update(number=item['number'])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@user_passes_test(is_secretary)
def remove_from_heat(request, assignment_id):
    assignment = get_object_or_404(HeatAssignment, id=assignment_id)
    # Нельзя удалять, если есть результат
    if assignment.result_time:
        return JsonResponse({'success': False, 'error': 'Нельзя удалить участника с результатом'})
    assignment.delete()
    return JsonResponse({'success': True})

def group_heats_data(request, pk):
    cat_id = request.GET.get('cat')
    disc_id = request.GET.get('disc')
    heats = Heat.objects.filter(competition_id=pk, age_category_id=cat_id, discipline_id=disc_id)
    data = []
    for h in heats:
        taken = h.assignments.count()
        free = h.competition.lanes - taken  # TODO: брать из comp.lanes
        data.append({'id': h.id, 'number': h.number, 'taken': taken, 'free': free})
    return JsonResponse(data, safe=False)

def registered_athletes(request, pk):
    q = request.GET.get('q', '').lower()
    regs = Registration.objects.filter(competition_id=pk)
    if q:
        regs = regs.filter(Q(athlete__user__first_name__icontains=q) | Q(athlete__user__last_name__icontains=q))
    data = [{'id': r.athlete.id, 'name': r.athlete.user.get_full_name(), 'discipline': str(r.discipline)} for r in regs[:100]]
    return JsonResponse(data, safe=False)

@user_passes_test(is_secretary)
def finish_competition(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    comp.status = 'finished'
    comp.save()
    
    from activity.models import Activity
    from users.models import Achievement
    
    # Собираем победителей по каждой дисциплине
    for heat in comp.heats.all():
        for assignment in heat.assignments.filter(place__lte=3):
            athlete = assignment.registration.athlete
            place = assignment.place
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(place, '')
            
            # Запись в ленту активности
            Activity.objects.create(
                user=athlete.user,
                activity_type='achievement',
                title=f'{athlete.user.get_full_name()} занял {place} место',
                description=f'{heat.discipline.get_style_display()} {heat.discipline.distance}м — {comp.title}',
                link=f'/athlete/{athlete.user.username}/'
            )
            
            # Создаём достижение
            Achievement.objects.create(
                athlete=athlete,
                title=f'{medal} {place} место — {heat.discipline.get_style_display()} {heat.discipline.distance}м',
                achievement_type='medal',
                description=f'{comp.title} ({comp.start_date})',
                competition=comp.title,
                date=comp.start_date
            )
            
            # Проверка рекорда школы
            existing_record = Achievement.objects.filter(
                athlete=athlete,
                achievement_type='record',
                title__contains=heat.discipline.get_style_display()
            ).first()
            
            if not existing_record:
                # Если нет рекорда — создаём
                Achievement.objects.create(
                    athlete=athlete,
                    title=f'⭐ Рекорд школы — {heat.discipline.get_style_display()} {heat.discipline.distance}м',
                    achievement_type='record',
                    description=f'{assignment.result_time} — {comp.title}',
                    date=comp.start_date
                )
    
    # Общая запись в ленту
    Activity.objects.create(
        user=request.user,
        activity_type='competition',
        title=f'Соревнование «{comp.title}» завершено!',
        description=f'Поздравляем всех участников и победителей!',
        link=f'/competitions/{comp.pk}/results/'
    )
    
    messages.success(request, 'Соревнование завершено! Результаты опубликованы.')
    return redirect('public_results', pk=pk)

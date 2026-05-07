from __future__ import annotations

import re


TIME_RE = re.compile(r"^\d{1,2}:\d{2}[.,]\d{2,3}$")


def normalize_result_time(value: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", ".")
    if not TIME_RE.match(text):
        return None
    return text


def result_time_to_seconds(value: str) -> float:
    normalized = normalize_result_time(value)
    if not normalized:
        raise ValueError("Invalid result time format")
    minutes, sec_ms = normalized.split(":")
    seconds, millis = sec_ms.split(".")
    return int(minutes) * 60 + int(seconds) + (int(millis) / (1000 if len(millis) == 3 else 100))


def assign_places_by_time(assignments):
    ranked = sorted(assignments, key=lambda a: result_time_to_seconds(a.result_time))
    current_place = 1
    prev_time = None
    for index, assignment in enumerate(ranked):
        current_time = result_time_to_seconds(assignment.result_time)
        if prev_time is not None and current_time > prev_time:
            current_place = index + 1
        assignment.place = current_place
        prev_time = current_time
    return ranked


def build_heats_for_competition(comp, disciplines, age_categories, registrations_model, heat_model, assignment_model):
    for discipline in disciplines:
        for age_cat in age_categories:
            regs = registrations_model.objects.filter(
                competition=comp,
                discipline=discipline,
                athlete__birth_date__year__gte=age_cat.birth_year_from,
                athlete__birth_date__year__lte=age_cat.birth_year_to,
                athlete__gender=age_cat.gender,
            ).order_by("preliminary_time")
            if not regs.exists():
                continue

            reg_list = list(regs)
            lanes = comp.lanes
            heats_needed = (len(reg_list) + lanes - 1) // lanes
            for h in range(heats_needed):
                heat = heat_model.objects.create(
                    competition=comp,
                    discipline=discipline,
                    age_category=age_cat,
                    number=h + 1,
                )
                start = h * lanes
                heat_regs = reg_list[start : start + lanes]
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
                        assignment_model.objects.create(heat=heat, registration=reg, lane=lane_order[i] + 1)


def process_application_worksheet(
    ws,
    comp,
    coach,
    branch,
    user_model,
    athlete_profile_model,
    discipline_model,
    registration_model,
):
    style_map = {
        "вольный стиль": "free",
        "на спине": "back",
        "брасс": "breast",
        "баттерфляй": "fly",
        "комплекс": "medley",
    }
    created = 0
    duplicates = 0
    skipped = 0
    errors = []

    for row_number, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        last_name = (str(row[0]).strip() if row and row[0] is not None else "")
        first_name = (str(row[1]).strip() if row and len(row) > 1 and row[1] is not None else "")
        if not last_name or not first_name:
            skipped += 1
            continue
        try:
            gender = row[2] if len(row) > 2 else "M"
            birth_year = int(row[3]) if len(row) > 3 and row[3] not in (None, "") else 2010
            style = row[4] if len(row) > 4 else "Вольный стиль"
            distance = row[5] if len(row) > 5 else 50
            prelim_time = row[6] if len(row) > 6 else ""

            user, _ = user_model.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={"username": f"{last_name}_{first_name}_{birth_year}".lower()},
            )
            athlete, _ = athlete_profile_model.objects.get_or_create(
                user=user,
                defaults={
                    "birth_date": f"{birth_year}-01-01",
                    "gender": "M" if str(gender).upper() in ["M", "М"] else "F",
                },
            )
            athlete.gender = "M" if str(gender).upper() in ["M", "М"] else "F"
            athlete.save(update_fields=["gender"])

            style_code = style_map.get(str(style).strip().lower(), "free")
            distance_int = int(distance) if distance not in (None, "") else 50
            discipline, _ = discipline_model.objects.get_or_create(
                competition=comp, style=style_code, distance=distance_int
            )
            _, is_new = registration_model.objects.get_or_create(
                competition=comp,
                athlete=athlete,
                discipline=discipline,
                defaults={"preliminary_time": str(prelim_time or ""), "coach": coach, "branch": branch},
            )
            if is_new:
                created += 1
            else:
                duplicates += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Строка {row_number}: {exc}")

    return {
        "created": created,
        "duplicates": duplicates,
        "skipped": skipped,
        "errors": errors,
    }

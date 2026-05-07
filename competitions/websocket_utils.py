"""
Утилиты для WebSocket оптимизации - delta updates вместо full state.
"""
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_delta_result_update(assignment):
    """
    Отправить delta-обновление результата (без полной перезагрузки заплыва).
    Отправляет только изменённые поля:
    - result_time
    - place (если установлено)
    - status
    """
    channel_layer = get_channel_layer()
    
    # Собираем delta с только изменёнными данными
    delta = {
        'assignment_id': assignment.id,
        'result_time': assignment.result_time,
        'place': assignment.place,
        'status': assignment.status,
        'heat_id': assignment.heat_id,
    }
    
    async_to_sync(channel_layer.group_send)(
        f"competition_{assignment.heat.competition_id}",
        {
            "type": "result_delta_updated",
            "competition_id": assignment.heat.competition_id,
            "delta": delta,
        },
    )


def send_heat_delta_update(heat, assignments=None):
    """
    Отправить delta-обновление для заплыва.
    Используется после финализации дисциплины.
    """
    if assignments is None:
        assignments = heat.assignments.all()
    
    channel_layer = get_channel_layer()
    
    # Собираем delta для всех assignments в заплыве
    deltas = []
    for assignment in assignments:
        deltas.append({
            'assignment_id': assignment.id,
            'result_time': assignment.result_time,
            'place': assignment.place,
            'status': assignment.status,
        })
    
    async_to_sync(channel_layer.group_send)(
        f"competition_{heat.competition_id}",
        {
            "type": "heat_delta_updated",
            "competition_id": heat.competition_id,
            "heat_id": heat.id,
            "deltas": deltas,
        },
    )


def broadcast_heat_status_change(heat, new_status):
    """
    Отправить уведомление об изменении статуса заплыва.
    new_status: 'started', 'finished', 'cancelled', etc.
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f"competition_{heat.competition_id}",
        {
            "type": "heat_status_changed",
            "competition_id": heat.competition_id,
            "heat_id": heat.id,
            "status": new_status,
        },
    )


def broadcast_live_event(competition, event_type, data):
    """
    Отправить произвольное live-событие.
    event_type: 'heat_started', 'heat_finished', 'announcement', etc.
    """
    channel_layer = get_channel_layer()
    
    payload = {
        "type": "live_event",
        "competition_id": competition.id,
        "event_type": event_type,
        "data": data,
    }
    
    async_to_sync(channel_layer.group_send)(
        f"competition_{competition.id}",
        payload,
    )

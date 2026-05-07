import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CompetitionLiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.competition_id = self.scope["url_route"]["kwargs"]["competition_id"]
        self.group_name = f"competition_{self.competition_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Legacy endpoint - kept for backwards compatibility
    async def competition_result_updated(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "result_updated",
                    "competition_id": event["competition_id"],
                    "heat_id": event["heat_id"],
                    "assignment_id": event["assignment_id"],
                }
            )
        )

    # New optimized delta update
    async def result_delta_updated(self, event):
        """
        Отправить только изменённые данные результата (delta update).
        Клиент обновляет только одну ячейку вместо всего заплыва.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "result_delta_updated",
                    "competition_id": event["competition_id"],
                    "delta": event["delta"],
                }
            )
        )

    # Heat-level delta update
    async def heat_delta_updated(self, event):
        """
        Отправить delta-обновление для всего заплыва (после финализации).
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "heat_delta_updated",
                    "competition_id": event["competition_id"],
                    "heat_id": event["heat_id"],
                    "deltas": event["deltas"],
                }
            )
        )

    # Heat status change event
    async def heat_status_changed(self, event):
        """
        Уведомление об изменении статуса заплыва.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "heat_status_changed",
                    "competition_id": event["competition_id"],
                    "heat_id": event["heat_id"],
                    "status": event["status"],
                }
            )
        )

    # Generic live event
    async def live_event(self, event):
        """
        Отправить произвольное live-событие.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "live_event",
                    "competition_id": event["competition_id"],
                    "event_type": event.get("event_type"),
                    "data": event.get("data"),
                }
            )
        )

    async def competition_discipline_finalized(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "discipline_finalized",
                    "competition_id": event["competition_id"],
                    "discipline_id": event["discipline_id"],
                    "category_id": event["category_id"],
                }
            )
        )

    async def competition_finished(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "competition_finished",
                    "competition_id": event["competition_id"],
                }
            )
        )

    async def competition_heats_regenerated(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "heats_regenerated",
                    "competition_id": event["competition_id"],
                }
            )
        )

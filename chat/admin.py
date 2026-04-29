from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'created_at')
    list_filter = ('room_type',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'text_preview', 'created_at', 'is_read')
    list_filter = ('is_read', 'room')

    def text_preview(self, obj):
        return obj.text[:50]
    text_preview.short_description = 'Текст'

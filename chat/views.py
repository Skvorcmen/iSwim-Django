from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import ChatRoom, Message
from users.auth import has_role
from users.models import User
from trainers.models import Trainer

@login_required
def chat_list(request):
    rooms = request.user.chat_rooms.all()
    rooms_with_data = []
    for room in rooms:
        unread = room.messages.filter(is_read=False).exclude(sender=request.user).count()
        rooms_with_data.append({
            'room': room,
            'last_message': room.last_message(),
            'unread': unread,
        })
    return render(request, 'chat/chat_list.html', {'rooms': rooms_with_data})

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    messages = room.messages.all()[:50]
    room.messages.exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/chat_room.html', {
        'room': room,
        'messages': messages,
    })

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        participants_ids = request.POST.getlist('participants')
        room_type = request.POST.get('room_type', 'private')

        if not name or not participants_ids:
            return redirect('chat_list')

        room = ChatRoom.objects.create(
            name=name,
            room_type=room_type,
            created_by=request.user,
        )
        room.participants.add(request.user)
        for pid in participants_ids:
            if str(request.user.id) != pid:
                room.participants.add(int(pid))

        return redirect('chat_room', room_id=room.id)

    users = User.objects.exclude(id=request.user.id)
    context = {'users': users}
    if has_role(request.user, 'trainer', 'admin'):
        context['can_create_group'] = True
    return render(request, 'chat/create_room.html', context)

@login_required
def get_users(request):
    search = request.GET.get('search', '')
    users = User.objects.filter(
        Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search)
    ).exclude(id=request.user.id)[:20]
    data = [{'id': u.id, 'name': u.get_full_name() or u.email, 'avatar': u.avatar.url if u.avatar else ''} for u in users]
    return JsonResponse({'users': data})

@login_required
def unread_count(request):
    count = Message.objects.filter(
        room__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    return JsonResponse({'count': count})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.models import AthleteProfile
from athlete_stats.models import PersonalRecord, AthleteResult
from competitions.models import Competition
from .serializers import PersonalRecordSerializer, AthleteResultSerializer, CompetitionSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stats(request):
    athlete = get_object_or_404(AthleteProfile, user=request.user)
    
    personal_records = PersonalRecord.objects.filter(athlete=athlete)
    results = AthleteResult.objects.filter(athlete=athlete).order_by('-date')[:10]
    
    return Response({
        'personal_records': PersonalRecordSerializer(personal_records, many=True).data,
        'recent_results': AthleteResultSerializer(results, many=True).data,
    })

@api_view(['GET'])
def competitions_list(request):
    competitions = Competition.objects.filter(status='finished').order_by('-start_date')
    return Response(CompetitionSerializer(competitions, many=True).data)

@api_view(['GET'])
def competition_results(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    results = AthleteResult.objects.filter(competition=competition).select_related('athlete', 'discipline')
    return Response(AthleteResultSerializer(results, many=True).data)

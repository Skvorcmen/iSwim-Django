from rest_framework import serializers
from competitions.models import Competition, Discipline
from athlete_stats.models import AthleteResult, PersonalRecord
from users.models import AthleteProfile

class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ['id', 'title', 'location', 'start_date', 'end_date', 'status']

class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ['id', 'style', 'distance']

class PersonalRecordSerializer(serializers.ModelSerializer):
    discipline_name = serializers.CharField(source='discipline.__str__')
    
    class Meta:
        model = PersonalRecord
        fields = ['id', 'discipline_name', 'result_time', 'date']

class AthleteResultSerializer(serializers.ModelSerializer):
    discipline_name = serializers.CharField(source='discipline.__str__')
    competition_name = serializers.CharField(source='competition.title')
    
    class Meta:
        model = AthleteResult
        fields = ['id', 'discipline_name', 'result_time', 'place', 'date', 'competition_name']

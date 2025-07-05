from rest_framework import serializers
from .models import Score, Part, Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

class PartSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True, read_only=True)

    class Meta:
        model = Part
        fields = '__all__'

class ScoreSerializer(serializers.ModelSerializer):
    parts = PartSerializer(many=True, read_only=True)

    class Meta:
        model = Score
        fields = '__all__'

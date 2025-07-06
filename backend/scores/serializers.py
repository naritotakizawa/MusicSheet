from rest_framework import serializers
from .models import Score, Part, Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'pitch', 'duration', 'position', 'rest']

class PartSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True)

    class Meta:
        model = Part
        fields = ['id', 'name', 'notes']

class ScoreSerializer(serializers.ModelSerializer):
    parts = PartSerializer(many=True)

    class Meta:
        model = Score
        fields = ['id', 'title', 'created_at', 'updated_at', 'parts']

    def create(self, validated_data):
        parts_data = validated_data.pop('parts')
        score = Score.objects.create(**validated_data)
        for part_data in parts_data:
            notes_data = part_data.pop('notes')
            part = Part.objects.create(score=score, **part_data)
            for note_data in notes_data:
                Note.objects.create(part=part, **note_data)
        return score

    def update(self, instance, validated_data):
        # Update Score instance
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        # Handle nested Parts
        parts_data = validated_data.pop('parts')
        existing_parts = {part.id: part for part in instance.parts.all()}
        parts_to_keep = []

        for part_data in parts_data:
            part_id = part_data.get('id', None)
            if part_id in existing_parts:
                # Update existing part
                part = existing_parts[part_id]
                part.name = part_data.get('name', part.name)
                part.save()
                parts_to_keep.append(part.id)

                # Handle nested Notes within the part
                notes_data = part_data.pop('notes')
                existing_notes = {note.id: note for note in part.notes.all()}
                notes_to_keep = []

                for note_data in notes_data:
                    note_id = note_data.get('id', None)
                    if note_id in existing_notes:
                        # Update existing note
                        note = existing_notes[note_id]
                        note.pitch = note_data.get('pitch', note.pitch)
                        note.duration = note_data.get('duration', note.duration)
                        note.position = note_data.get('position', note.position)
                        note.rest = note_data.get('rest', note.rest)
                        note.save()
                        notes_to_keep.append(note.id)
                    else:
                        # Create new note
                        Note.objects.create(part=part, **note_data)

                # Delete notes that are no longer present
                for note_id, note in existing_notes.items():
                    if note_id not in notes_to_keep:
                        note.delete()

            else:
                # Create new part
                notes_data = part_data.pop('notes')
                part = Part.objects.create(score=instance, **part_data)
                for note_data in notes_data:
                    Note.objects.create(part=part, **note_data)

        # Delete parts that are no longer present
        for part_id, part in existing_parts.items():
            if part_id not in parts_to_keep:
                part.delete()

        return instance

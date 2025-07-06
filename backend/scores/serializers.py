from rest_framework import serializers
from .models import Score, Part, Measure, Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'pitch', 'duration', 'position', 'rest']

class MeasureSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True)

    class Meta:
        model = Measure
        fields = ['id', 'number', 'notes']


class PartSerializer(serializers.ModelSerializer):
    measures = MeasureSerializer(many=True)

    class Meta:
        model = Part
        fields = ['id', 'name', 'measures']

class ScoreSerializer(serializers.ModelSerializer):
    parts = PartSerializer(many=True)

    class Meta:
        model = Score
        fields = ['id', 'title', 'created_at', 'updated_at', 'parts']

    def _trim_notes(self, notes):
        duration_map = {'w': 4, 'h': 2, 'q': 1, '8': 0.5, '16': 0.25}
        beats = 0
        trimmed = []
        for note in notes:
            beats += duration_map.get(note.get('duration'), 0)
            if beats > 4:
                break
            trimmed.append(note)
        return trimmed

    def create(self, validated_data):
        parts_data = validated_data.pop('parts')
        score = Score.objects.create(**validated_data)
        for part_data in parts_data:
            measures_data = part_data.pop('measures')
            part = Part.objects.create(score=score, **part_data)
            for measure_data in measures_data:
                notes_data = self._trim_notes(measure_data.pop('notes'))
                measure = Measure.objects.create(part=part, **measure_data)
                for idx, note_data in enumerate(notes_data):
                    Note.objects.create(measure=measure, **note_data)
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
                part = existing_parts[part_id]
                part.name = part_data.get('name', part.name)
                part.save()
                parts_to_keep.append(part.id)

                measures_data = part_data.pop('measures')
                existing_measures = {m.id: m for m in part.measures.all()}
                measures_to_keep = []

                for measure_data in measures_data:
                    measure_id = measure_data.get('id', None)
                    notes_data = self._trim_notes(measure_data.pop('notes'))
                    if measure_id in existing_measures:
                        measure = existing_measures[measure_id]
                        measure.number = measure_data.get('number', measure.number)
                        measure.save()
                        measures_to_keep.append(measure.id)
                        existing_notes = {n.id: n for n in measure.notes.all()}
                        notes_to_keep = []
                        for note_data in notes_data:
                            note_id = note_data.get('id', None)
                            if note_id in existing_notes:
                                note = existing_notes[note_id]
                                note.pitch = note_data.get('pitch', note.pitch)
                                note.duration = note_data.get('duration', note.duration)
                                note.position = note_data.get('position', note.position)
                                note.rest = note_data.get('rest', note.rest)
                                note.save()
                                notes_to_keep.append(note.id)
                            else:
                                Note.objects.create(measure=measure, **note_data)
                        for nid, note in existing_notes.items():
                            if nid not in notes_to_keep:
                                note.delete()
                    else:
                        measure = Measure.objects.create(part=part, **measure_data)
                        measures_to_keep.append(measure.id)
                        for idx, note_data in enumerate(notes_data):
                            Note.objects.create(measure=measure, **note_data)
                for mid, meas in existing_measures.items():
                    if mid not in measures_to_keep:
                        meas.delete()

            else:
                measures_data = part_data.pop('measures')
                part = Part.objects.create(score=instance, **part_data)
                for measure_data in measures_data:
                    notes_data = self._trim_notes(measure_data.pop('notes'))
                    measure = Measure.objects.create(part=part, **measure_data)
                    for idx, note_data in enumerate(notes_data):
                        Note.objects.create(measure=measure, **note_data)

        # Delete parts that are no longer present
        for part_id, part in existing_parts.items():
            if part_id not in parts_to_keep:
                part.delete()

        return instance

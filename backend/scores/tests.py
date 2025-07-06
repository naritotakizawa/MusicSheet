from django.test import TestCase
from .serializers import ScoreSerializer
from .models import Score, Part, Measure, Note


class ScoreSerializerTests(TestCase):
    def test_create_score_with_measures(self):
        data = {
            'title': 'Test',
            'parts': [
                {
                    'name': 'P1',
                    'measures': [
                        {
                            'number': 1,
                            'notes': [
                                {'pitch': 'C4', 'duration': 'q', 'rest': False, 'position': 0},
                                {'pitch': 'D4', 'duration': 'q', 'rest': False, 'position': 1},
                            ]
                        }
                    ]
                }
            ]
        }
        serializer = ScoreSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        score = serializer.save()
        self.assertEqual(score.parts.count(), 1)
        part = score.parts.first()
        self.assertEqual(part.measures.count(), 1)
        measure = part.measures.first()
        self.assertEqual(measure.notes.count(), 2)

    def test_trim_extra_notes_on_update(self):
        score = Score.objects.create(title='T')
        part = Part.objects.create(score=score, name='P1')
        measure = Measure.objects.create(part=part, number=1)
        Note.objects.create(measure=measure, pitch='C4', duration='q', rest=False, position=0)

        update_data = {
            'title': 'T',
            'parts': [
                {
                    'id': part.id,
                    'name': 'P1',
                    'measures': [
                        {
                            'id': measure.id,
                            'number': 1,
                            'notes': [
                                {'id': measure.notes.first().id, 'pitch': 'C4', 'duration': 'w', 'rest': False, 'position': 0},
                                {'pitch': 'D4', 'duration': 'q', 'rest': False, 'position': 1},
                            ]
                        }
                    ]
                }
            ]
        }
        serializer = ScoreSerializer(instance=score, data=update_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        score.refresh_from_db()
        self.assertEqual(score.parts.count(), 1)
        self.assertEqual(score.parts.first().measures.first().notes.count(), 1)

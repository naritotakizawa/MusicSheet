from django.db import models

class Score(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Part(models.Model):
    score = models.ForeignKey(Score, related_name='parts', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name} for {self.score.title}'

class Measure(models.Model):
    part = models.ForeignKey(Part, related_name='measures', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()

    def __str__(self):
        return f'Measure {self.number} of {self.part.name}'

class Note(models.Model):
    measure = models.ForeignKey(Measure, related_name='notes', on_delete=models.CASCADE)
    pitch = models.CharField(max_length=10)  # e.g., 'C4', 'G#5'
    duration = models.CharField(max_length=10)  # e.g., 'q', 'h', '8'
    position = models.PositiveIntegerField()
    rest = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.pitch} ({self.duration}) at {self.position}'
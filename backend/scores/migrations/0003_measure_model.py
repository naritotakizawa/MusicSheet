from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0002_note_rest'),
    ]

    operations = [
        migrations.CreateModel(
            name='Measure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measures', to='scores.part')),
            ],
        ),
        migrations.AddField(
            model_name='note',
            name='measure',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='scores.measure'),
        ),
        migrations.RemoveField(
            model_name='note',
            name='part',
        ),
    ]

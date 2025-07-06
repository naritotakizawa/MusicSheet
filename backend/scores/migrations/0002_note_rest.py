from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='rest',
            field=models.BooleanField(default=False),
        ),
    ]

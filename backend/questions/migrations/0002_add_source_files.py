from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='source_files',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]

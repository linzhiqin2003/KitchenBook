# Generated manually on 2026-05-02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_ailabconversation_agent_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='ailabmessage',
            name='file_attachment',
            field=models.JSONField(blank=True, null=True, help_text='文件附件元信息 {type, url, filename, size}'),
        ),
    ]

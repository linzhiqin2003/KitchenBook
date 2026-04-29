from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_ailabmessage_cache_tokens_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ailabconversation",
            name="agent_model",
            field=models.CharField(
                blank=True,
                default="deepseek-v4-flash",
                help_text="该会话选中的 Hermes 基座模型",
                max_length=100,
            ),
        ),
    ]

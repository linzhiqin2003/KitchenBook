# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_tag_blogpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredient',
            name='category',
            field=models.CharField(
                choices=[
                    ('meat', '肉类'),
                    ('seafood', '海鲜'),
                    ('vegetable', '蔬菜'),
                    ('seasoning', '调味料'),
                    ('staple', '主食/干货'),
                    ('dairy', '乳制品'),
                    ('other', '其他'),
                ],
                default='other',
                help_text='食材分类',
                max_length=20,
            ),
        ),
    ]


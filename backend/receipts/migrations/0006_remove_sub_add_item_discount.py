from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("receipts", "0005_receiptimage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="receiptitem",
            name="category_sub",
        ),
        migrations.AddField(
            model_name="receiptitem",
            name="discount",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=10
            ),
        ),
    ]

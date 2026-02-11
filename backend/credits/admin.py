from django.contrib import admin
from .models import CreditBalance, CreditTransaction
from .services import add_credits


@admin.register(CreditBalance)
class CreditBalanceAdmin(admin.ModelAdmin):
    list_display = ["user", "balance_seconds", "balance_minutes", "updated_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["updated_at"]

    @admin.display(description="Balance (min)")
    def balance_minutes(self, obj):
        return f"{obj.balance_seconds // 60}m {obj.balance_seconds % 60}s"

    # Admin actions: grant credits to selected users
    actions = ["grant_60min", "grant_300min"]

    @admin.action(description="Grant 60 minutes")
    def grant_60min(self, request, queryset):
        for bal in queryset:
            add_credits(
                bal.user, 3600,
                tx_type=CreditTransaction.TxType.GRANT,
                description="Admin grant: 60min",
            )

    @admin.action(description="Grant 300 minutes")
    def grant_300min(self, request, queryset):
        for bal in queryset:
            add_credits(
                bal.user, 18000,
                tx_type=CreditTransaction.TxType.GRANT,
                description="Admin grant: 300min",
            )


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ["id_short", "user", "tx_type", "amount_seconds", "balance_after", "created_at"]
    list_filter = ["tx_type", "created_at"]
    search_fields = ["user__username", "user__email", "apple_transaction_id"]
    readonly_fields = [
        "id", "user", "tx_type", "amount_seconds", "balance_after",
        "description", "apple_transaction_id", "apple_product_id", "created_at",
    ]

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8]

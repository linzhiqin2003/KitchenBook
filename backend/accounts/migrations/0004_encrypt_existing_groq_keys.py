"""Encrypt existing plaintext groq_api_key values in the database.

Uses raw SQL to avoid EncryptedCharField's auto-encrypt in get_prep_value
(which would double-encrypt if we used ORM .save()).
"""

from django.db import migrations


def encrypt_forward(apps, schema_editor):
    """Encrypt plaintext keys (those starting with 'gsk_')."""
    from accounts.crypto import encrypt_api_key

    UserProfile = apps.get_model("accounts", "UserProfile")
    db_alias = schema_editor.connection.alias

    # Read rows with raw SQL to bypass EncryptedCharField.from_db_value
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, groq_api_key FROM accounts_userprofile "
            "WHERE groq_api_key != '' AND groq_api_key LIKE 'gsk_%%'"
        )
        rows = cursor.fetchall()

    for row_id, plaintext_key in rows:
        encrypted = encrypt_api_key(plaintext_key)
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE accounts_userprofile SET groq_api_key = %s WHERE id = %s",
                [encrypted, row_id],
            )


def encrypt_reverse(apps, schema_editor):
    """Decrypt keys back to plaintext for rollback."""
    from accounts.crypto import decrypt_api_key

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, groq_api_key FROM accounts_userprofile "
            "WHERE groq_api_key != '' AND groq_api_key NOT LIKE 'gsk_%%'"
        )
        rows = cursor.fetchall()

    for row_id, encrypted_key in rows:
        plaintext = decrypt_api_key(encrypted_key)
        if plaintext:
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE accounts_userprofile SET groq_api_key = %s WHERE id = %s",
                    [plaintext, row_id],
                )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_userprofile_groq_api_key"),
    ]

    operations = [
        migrations.RunPython(encrypt_forward, encrypt_reverse),
    ]

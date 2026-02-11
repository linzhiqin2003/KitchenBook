"""Custom Django model field that transparently encrypts/decrypts values."""

from __future__ import annotations

from django.db import models


class EncryptedCharField(models.CharField):
    """CharField that stores Fernet-encrypted text in the database.

    * ``get_prep_value()`` encrypts before writing.
    * ``from_db_value()`` decrypts after reading.
    * ``deconstruct()`` returns the path of a plain ``CharField`` so that
      Django migrations never reference this custom field — no schema
      migration is needed when switching to / from encryption.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        from accounts.crypto import encrypt_api_key
        return encrypt_api_key(value)

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        from accounts.crypto import decrypt_api_key
        return decrypt_api_key(value)

    def deconstruct(self):
        name, _path, args, kwargs = super().deconstruct()
        # Present as a plain CharField so migrations stay agnostic
        return name, "django.db.models.CharField", args, kwargs

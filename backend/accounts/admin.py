from django.contrib import admin
from .models import UserProfile, Organization, OrganizationMember, InviteLink

admin.site.register(UserProfile)
admin.site.register(Organization)
admin.site.register(OrganizationMember)
admin.site.register(InviteLink)

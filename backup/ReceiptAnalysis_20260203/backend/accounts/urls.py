from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", views.UserProfileView.as_view(), name="auth-me"),
    path("orgs/", views.OrganizationListCreateView.as_view(), name="auth-orgs"),
    path("orgs/<uuid:org_id>/members/", views.OrganizationMembersView.as_view(), name="auth-org-members"),
    path("orgs/<uuid:org_id>/invite/", views.InviteLinkCreateView.as_view(), name="auth-org-invite"),
    path("orgs/<uuid:org_id>/leave/", views.LeaveOrgView.as_view(), name="auth-org-leave"),
    path("orgs/<uuid:org_id>/members/<int:member_id>/remove/", views.RemoveMemberView.as_view(), name="auth-org-remove-member"),
    path("orgs/<uuid:org_id>/", views.DissolveOrgView.as_view(), name="auth-org-dissolve"),
    path("invite/<uuid:invite_id>/accept/", views.InviteAcceptView.as_view(), name="auth-invite-accept"),
]

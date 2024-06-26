# Copyright (c) 2023 SplitFree Org.
# urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from split_free_backend.core.views import (
    AcceptInviteView,
    ActivityView,
    BalanceView,
    DebtView,
    EmailActivateView,
    ExpenseDetailView,
    ExpenseView,
    GroupDetailView,
    GroupView,
    InviteGenerateView,
    LogoutView,
    MemberDetailView,
    MemberView,
    UserDetailView,
    UserInfoView,
    UserView,
)

urlpatterns = [
    path("activities/", ActivityView.as_view(), name="activity-list"),
    path("balances/", BalanceView.as_view(), name="balance-list"),
    path("debts/", DebtView.as_view(), name="debt-list"),
    path("members/", MemberView.as_view(), name="member-list"),
    path("members/<int:pk>/", MemberDetailView.as_view(), name="member-detail"),
    path("groups/", GroupView.as_view(), name="group-list"),
    path("groups/<int:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("expenses/", ExpenseView.as_view(), name="expense-list"),
    path("expenses/<int:pk>/", ExpenseDetailView.as_view(), name="expense-detail"),
    # Token authentication
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Invite link
    path("invite/accept/", AcceptInviteView.as_view(), name="invite-accept"),
    path("invite/generate/", InviteGenerateView.as_view(), name="invite-generate"),
    # Authentication
    path("user_info/", UserInfoView.as_view(), name="user-info"),
    path("users/", UserView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    # Email
    path(
        "email/activate/<str:token>/",
        EmailActivateView.as_view(),
        name="email-activate",
    ),
]

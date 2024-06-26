# Copyright (c) 2023 SplitFree Org.
from copy import copy
from datetime import timedelta
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from split_free_backend.core.helpers import get_auth_headers
from split_free_backend.core.models import (
    Activity,
    Balance,
    Debt,
    Expense,
    Group,
    InviteToken,
    Member,
    User,
)
from split_free_backend.core.serializers import (
    ExpenseSerializer,
    GroupSerializer,
    MemberSerializer,
)


class BaseAPITestCase(TestCase):
    def setUp(self):
        super().setUp()
        # Create a test user
        self.user = User.objects.create(
            email="testuser@splitmail.com",
            password="testpassword",
            is_active=True,
        )

        # Obtain a valid access token for the test user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)


class MemberCRUDTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Create a group for testing
        self.group = Group.objects.create(
            title="Test Group",
            description="Group for testing",
        )
        self.group.users.add(self.user)

    def test_create_member(self):
        # Set up
        data = {"name": "Apo", "group": self.group.id}

        # Action
        response = self.client.post(
            "/api/members/",
            data,
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(Member.objects.get().name, "Apo")

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'{self.user.name} added member "Apo" to group "{self.group.title}"',
        )
        self.assertEqual(Activity.objects.get().group, self.group)

    def test_read_member(self):
        # Setup
        member = Member.objects.create(name="Michael", group=self.group)

        # Action
        response = self.client.get(
            f"/api/members/{member.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MemberSerializer(member).data)

    def test_update_member(self):
        # Setup
        member = Member.objects.create(name="Apo", group=self.group)

        # Action
        data = {"name": "Apo Jean", "group": self.group.id}

        # Checks
        response = self.client.put(
            f"/api/members/{member.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.name, "Apo Jean")

    def test_delete_member(self):
        # Setup
        member = Member.objects.create(name="Michael", group=self.group)
        Balance.objects.create(owner=member, group=self.group)

        # Action
        response = self.client.delete(
            f"/api/members/{member.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Member.objects.count(), 0)

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'{self.user.name} removed member "{member.name}" from group "{member.group.title}"',
        )
        self.assertEqual(Activity.objects.get().group, self.group)

    def test_delete_member_who_paid_expense(self):
        # Setup
        member1 = Member.objects.create(name="Michael", group=self.group)
        member2 = Member.objects.create(name="Apojean", group=self.group)
        Balance.objects.create(owner=member1, group=self.group)
        Balance.objects.create(owner=member2, group=self.group)

        data = {
            "amount": 40.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": member1.id,
            "group": self.group.id,
            "participants": [member2.id],
        }

        self.client.post(
            "/api/expenses/",
            data,
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 12
        self.assertEqual(Balance.objects.count(), 2)
        self.assertEqual(Balance.objects.first().amount, -40)
        self.assertEqual(Balance.objects.last().amount, 40)
        self.assertEqual(Debt.objects.first().amount, 40)
        self.assertEqual(Debt.objects.count(), 1)

        # Action
        self.client.delete(
            f"/api/members/{member1.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 2
        self.assertEqual(Balance.objects.count(), 1)
        self.assertEqual(Balance.objects.get().amount, 0)
        self.assertEqual(Debt.objects.count(), 0)

        # Further Action
        response = self.client.delete(
            f"/api/expenses/{Expense.objects.get().id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 3
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(Debt.objects.count(), 0)

    def test_delete_member_who_participated_expense(self):
        # Setup
        member1 = Member.objects.create(name="Michael", group=self.group)
        member2 = Member.objects.create(name="Apojean", group=self.group)
        Balance.objects.create(owner=member1, group=self.group)
        Balance.objects.create(owner=member2, group=self.group)

        data = {
            "amount": 40.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": member1.id,
            "group": self.group.id,
            "participants": [member2.id],
        }

        self.client.post(
            "/api/expenses/",
            data,
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 12
        self.assertEqual(Balance.objects.count(), 2)
        self.assertEqual(Balance.objects.first().amount, -40)
        self.assertEqual(Balance.objects.last().amount, 40)
        self.assertEqual(Debt.objects.first().amount, 40)
        self.assertEqual(Debt.objects.count(), 1)

        # Action
        self.client.delete(
            f"/api/members/{member2.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 2
        self.assertEqual(Balance.objects.count(), 1)
        self.assertEqual(Balance.objects.get().amount, 0)
        self.assertEqual(Debt.objects.count(), 0)

        # Further Action
        response = self.client.delete(
            f"/api/expenses/{Expense.objects.get().id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks 3
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(Debt.objects.count(), 0)


class GroupCRUDTests(BaseAPITestCase):
    def create_group_with_orm(self):
        self.group = Group.objects.create(title="Anniversary", description="Special day")
        self.group.users.add(self.user)
        # Create two members for this group
        self.members = [
            Member.objects.create(name="Member1", group=self.group),
            Member.objects.create(name="Member2", group=self.group),
        ]

    def test_create_group(self):
        # Setup
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "member_names": ["Michael", "Apollon"],  # Guess who autocompleted that
        }

        # Action
        response = self.client.post(
            "/api/groups/",
            data,
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        created_group = Group.objects.get()
        self.assertEqual(created_group.title, "Birthday Party")
        self.assertEqual(created_group.members.count(), 2)

        activities = Activity.objects.all()

        self.assertEqual(Activity.objects.count(), 3)
        self.assertEqual(
            activities[0].text,
            f'{self.user.name} created group "Birthday Party"',
        )
        self.assertEqual(activities[0].group, created_group)

        self.assertEqual(
            activities[1].text,
            f'{self.user.name} added member "Michael" to group "Birthday Party"',
        )
        self.assertEqual(activities[1].group, created_group)

        self.assertEqual(
            activities[2].text,
            f'{self.user.name} added member "Apollon" to group "Birthday Party"',
        )
        self.assertEqual(activities[2].group, created_group)

    def test_create_group_without_description(self):
        # Setup
        data = {
            "title": "Birthday Party",
            "member_names": ["Michael", "Apojean"],
        }

        # Action
        response = self.client.post(
            "/api/groups/",
            data,
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)

    def test_read_group(self):
        # Setup
        self.create_group_with_orm()

        # Action
        response = self.client.get(
            f"/api/groups/{self.group.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, GroupSerializer(self.group).data)

    def test_update_group(self):
        # Setup
        self.create_group_with_orm()
        data = {
            "title": "Workshop",
            "description": "Interactive session",
            "member_names": ["Member2"],
        }

        # Action
        response = self.client.put(
            f"/api/groups/{self.group.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group_copy = copy(self.group)
        self.group.refresh_from_db()
        self.assertEqual(self.group.title, "Workshop")
        self.assertEqual(self.group.members.count(), 1)
        self.assertEqual(self.group.members.first().name, "Member2")

        activities = Activity.objects.all()
        self.assertEqual(Activity.objects.count(), 2)
        self.assertEqual(
            Activity.objects.first().text,
            f"{self.user.name} changed group title from \"{group_copy.title}\" to \"{data['title']}\"",
        )
        self.assertEqual(Activity.objects.first().group, self.group)
        self.assertEqual(
            activities[1].text,
            f'{self.user.name} changed group description from "{group_copy.description}" to '
            f"\"{data['description']}\"",
        )
        self.assertEqual(activities[1].group, self.group)

    def test_delete_group(self):
        # Setup
        self.create_group_with_orm()

        # Action
        response = self.client.delete(
            f"/api/groups/{self.group.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Group.objects.count(), 0)

    def test_no_access_to_other_users_groups(self):
        # Setup
        other_user = User.objects.create(email="otheruser@hotmail.com", password="otherpassword")
        other_group = Group.objects.create(
            title="Other Group",
            description="Group for testing",
        )
        other_group.users.add(other_user)
        response = self.client.get(
            f"/api/groups/{other_group.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(
            f"/api/groups/{other_group.id}/",
            {"title": "New Title", "description": "New Description"},
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(
            f"/api/groups/{other_group.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExpenseCRUDTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Create a group for testing
        self.group = Group.objects.create(
            title="Test Group",
            description="Group for testing",
        )
        self.group.users.add(self.user)

        # Create some members for testing
        self.member1 = Member.objects.create(name="Member1", group=self.group)
        self.member2 = Member.objects.create(name="Member2", group=self.group)

        # Create associated balances. This usually comes with the creation of
        # the group using the post method, but as we are unit testing we use the
        # ORM instead
        Balance.objects.create(owner=self.member1, group=self.group, amount=0.00)
        Balance.objects.create(owner=self.member2, group=self.group, amount=0.00)

    def test_create_expense(self):
        # Actions
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.member1.id,
            "group": self.group.id,
            "participants": [self.member1.id, self.member2.id],
        }
        response = self.client.post(
            "/api/expenses/",
            data,
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.member1)
        self.assertEqual(expense.currency, "EUR")
        self.assertEqual(list(expense.participants.all()), [self.member1, self.member2])

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'{self.user.name} added an expense "{expense.title}" of amount {expense.amount} {expense.currency} '
            f'to group "{self.group.title}"',
        )
        self.assertEqual(Activity.objects.get().group, self.group)

    def test_create_expense_without_description(self):
        # Actions
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "payer": self.member1.id,
            "group": self.group.id,
            "participants": [self.member1.id, self.member2.id],
        }
        response = self.client.post(
            "/api/expenses/",
            data,
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.member1)
        self.assertEqual(expense.currency, "EUR")
        self.assertEqual(list(expense.participants.all()), [self.member1, self.member2])

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'{self.user.name} added an expense "{expense.title}" of amount {expense.amount} {expense.currency} '
            f'to group "{self.group.title}"',
        )
        self.assertEqual(Activity.objects.get().group, self.group)

    def test_read_expense(self):
        # Setup
        expense = Expense.objects.create(
            amount=30.00,
            title="Lunch",
            description="Expense for lunch",
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1, self.member2])

        # Action
        response = self.client.get(
            f"/api/expenses/{expense.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ExpenseSerializer(expense).data)

    @patch("split_free_backend.core.signals.calculate_new_debts", side_effect=lambda group: None)
    def test_update_expense(self, _):
        # Setup
        expense = Expense.objects.create(
            amount=20.00,
            title="Coffee",
            description="Expense for coffee",
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1])

        # Action
        data = {
            "amount": 25.00,
            "title": "Tea",
            "description": "Expense for tea",
            "payer": self.member2.id,
            "group": self.group.id,
            "participants": [self.member2.id],
        }
        old_expense = copy(expense)
        old_expense_participants = expense._participants()
        response = self.client.put(
            f"/api/expenses/{expense.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 25.00)
        self.assertEqual(expense.title, "Tea")
        self.assertEqual(expense.payer, self.member2)
        self.assertEqual(list(expense.participants.all()), [self.member2])

        activities = Activity.objects.all()
        self.assertEqual(Activity.objects.count(), 5)
        self.assertEqual(
            activities[0].text,
            f'{self.user.name} changed expense "{old_expense.title}" amount from '
            f"{'{:.2f}'.format(old_expense.amount)} to {expense.amount}",
        )
        self.assertEqual(activities[0].group, self.group)
        self.assertEqual(
            activities[1].text,
            f'{self.user.name} changed expense "{old_expense.title}" title '
            f'from "{old_expense.title}" to "{expense.title}"',
        )
        self.assertEqual(activities[1].group, self.group)
        self.assertEqual(
            activities[2].text,
            f'{self.user.name} changed expense "{old_expense.title}" description '
            f'from "{old_expense.description}" to "{expense.description}"',
        )
        self.assertEqual(activities[2].group, self.group)
        self.assertEqual(
            activities[3].text,
            f'{self.user.name} changed expense "{old_expense.title}" payer '
            f'from "{old_expense.payer.name}" to "{expense.payer.name}"',
        )
        self.assertEqual(activities[3].group, self.group)
        self.assertEqual(
            activities[4].text,
            f'{self.user.name} changed expense "{old_expense.title}" participants '
            f'from "{old_expense_participants}" '
            f'to "{expense._participants()}"',
        )
        self.assertEqual(activities[4].group, self.group)

    def test_delete_expense(self):
        # Setup
        expense = Expense.objects.create(
            amount=40.00,
            title="Snacks",
            description="Expense for snacks",
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1, self.member2])

        # Action
        response = self.client.delete(
            f"/api/expenses/{expense.id}/",
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'{self.user.name} deleted expense "{expense.title}"',
        )
        self.assertEqual(Activity.objects.get().group, self.group)


class DebtTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.groups = [
            Group.objects.create(title="Friend group", description="This group is friendly"),
            Group.objects.create(title="Normal group", description="This group is normal"),
        ]

        self.groups[0].users.add(self.user)
        self.groups[1].users.add(self.user)

        self.members = [
            # Members of groups[0]
            Member.objects.create(name="Apo", group=self.groups[0]),
            Member.objects.create(name="Michael", group=self.groups[0]),
            Member.objects.create(name="George", group=self.groups[0]),
            # Members of groups[1]
            Member.objects.create(name="Apo", group=self.groups[1]),
            Member.objects.create(name="Michael", group=self.groups[1]),
        ]

    def test_get_all_debts(self):
        # Setup
        # Let's create some meaningful debts and get them all
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[0],
            lender=self.members[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[2],
            lender=self.members[1],
            amount=50.00,
        )

        Debt.objects.create(
            group=self.groups[1],
            borrower=self.members[1],
            lender=self.members[0],
            amount=10.00,
        )

        # Action
        response = self.client.get("/api/debts/", format="json", headers=get_auth_headers(self.access_token))

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_debts_by_group(self):
        # Setup
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[0],
            lender=self.members[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[2],
            lender=self.members[1],
            amount=50.00,
        )
        Debt.objects.create(
            group=self.groups[1],
            borrower=self.members[1],
            lender=self.members[0],
            amount=10.00,
        )

        # Action
        # Filter debts for a specific group (groups[0])
        response = self.client.get(
            "/api/debts/",
            {"group_id": self.groups[0].id},
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Ensure that all debts in the response belong to groups[0]
        for debt in response.data:
            self.assertEqual(debt["group"], self.groups[0].id)


#########################################################################
# Tests for invite token


class InviteTokenTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.group = Group.objects.create(title="Friend group", description="This group is friendly")
        self.group.users.add(self.user)

    def test_create_invite_token(self):
        # Action
        response = self.client.post(
            "/api/invite/generate/",
            {
                "group_id": self.group.id,
            },
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InviteToken.objects.count(), 1)
        invite_token = InviteToken.objects.first()
        self.assertEqual(response.data["invite_token"], invite_token.token)
        # instead of using equal on time fields, we can use assertAlmostEqual
        self.assertAlmostEqual(
            invite_token.expires_at,
            invite_token.created_at + timedelta(days=1),
            delta=timedelta(minutes=1),
        )

    def test_has_and_group_are_unique_together(self):
        # Create an invite token
        InviteToken.objects.create(
            group=self.group,
            token="123456",
        )

        # Try to create another invite token for the same group
        with self.assertRaises(IntegrityError):
            InviteToken.objects.create(
                group=self.group,
                token="123456",
            )

    def test_use_invite_token(self):
        # Setup
        # create another group
        another_group = Group.objects.create(title="Another group", description="This group is another")

        invite_token = InviteToken.objects.create(
            group=another_group,
        )

        # Action
        response = self.client.post(
            "/api/invite/accept/",
            {
                "invite_token": invite_token.token,
            },
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.expense_groups.count(), 2)
        self.assertEqual(self.user.expense_groups.first(), self.group)
        self.assertEqual(self.user.expense_groups.last(), another_group)

        self.assertEqual(Activity.objects.count(), 1)
        self.assertEqual(
            Activity.objects.get().text,
            f'New user has joined to group "{another_group.title}"',
        )
        self.assertEqual(Activity.objects.get().group, another_group)

        # Ensure that the invite token is deleted
        self.assertEqual(InviteToken.objects.count(), 0)

    def test_use_expired_invite_token(self):
        # Setup
        # create another group
        another_group = Group.objects.create(title="Another group", description="This group is another")

        invite_token = InviteToken.objects.create(
            group=another_group,
            token="123456",
            expires_at=timezone.now() - timedelta(days=1),
        )

        # Action
        response = self.client.post(
            "/api/invite/accept/",
            {
                "invite_token": invite_token.token,
            },
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invite token is expired")

    def test_use_invalid_invite_token(self):
        # Action
        response = self.client.post(
            "/api/invite/accept/",
            {
                "invite_token": "123",
            },
            format="json",
            headers=get_auth_headers(self.access_token),
        )

        # Checks
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

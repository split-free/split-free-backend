# Copyright (c) 2023 SplitFree Org.

from django.forms.models import model_to_dict
from rest_framework import generics

from split_free_all.models import Expense, Group, User
from split_free_all.serializers import (
    ExpenseSerializer,
    GroupSerializer,
    UserSerializer,
)
from split_free_all.signals import (
    expense_created,
    expense_destroyed,
    expense_updated,
    group_created,
)


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupList(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        group_created.send(sender=self.__class__, instance=serializer.instance)


class GroupDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ExpenseList(generics.ListCreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        expense_created.send(sender=self.__class__, instance=serializer.instance)


class ExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        old_expense_info = model_to_dict(instance)
        serializer.save()
        new_expense_info = model_to_dict(serializer.instance)

        if (
            old_expense_info["participants"] != new_expense_info["participants"]
            or old_expense_info["amount"] != new_expense_info["amount"]
            or old_expense_info["payer"] != new_expense_info["payer"]
        ):
            # Trigger the custom signal
            expense_updated.send(
                sender=self.__class__,
                instance=serializer.instance,
                old_expense_info=old_expense_info,
                new_expense_info=new_expense_info,
            )

    def perform_destroy(self, instance):
        instance = self.get_object()
        # Trigger the custom signal
        expense_destroyed.send(sender=self.__class__, instance=instance)

        instance.delete()

# Copyright (c) 2023 SplitFree Org.

from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'User("{self.name}")'


class Member(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Member("{self.name}")'


class Group(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Group("{self.title}")'


class Balance(models.Model):
    owner = models.ForeignKey(Member, blank=True, null=True, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Owner("{self.owner.name}"): {self.amount}'


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    currency = models.CharField(max_length=4, default="EUR")
    payer = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="payer"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    date = models.CharField(max_length=30, default="")
    participants = models.ManyToManyField(Member, related_name="participants")

    def __str__(self):
        return f'Expense("{self.title}") - Amount: {self.amount}'


class Debt(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    borrower = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="borrower"
    )
    lender = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="lender")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Debt({self.borrower.name} to {self.lender.name}): {self.amount}"

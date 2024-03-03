# Copyright (c) 2023 SplitFree Org.
# serializers.py
from django.core.mail import send_mail
from rest_framework import serializers

from split_free_all.models import (
    Activity,
    Balance,
    Debt,
    Expense,
    Group,
    InviteToken,
    Member,
    User,
)


class UserSerializer(serializers.ModelSerializer):
    # in case entry is for anon user lets not make email or password required
    email = serializers.EmailField(required=False)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, required=False
    )

    class Meta:
        model = User
        fields = ["email", "password", "is_anonymous"]

    def validate(self, data):
        if "is_anonymous" in data and data["is_anonymous"]:
            if "password" in data:
                raise serializers.ValidationError(
                    {"password": "This field is not required for anonymous user."}
                )
            if "email" in data:
                raise serializers.ValidationError(
                    {"email": "This field is not required for anonymous user."}
                )
            data["email"] = None
            data["password"] = None
            data["is_anonymous"] = True
        else:
            if "password" not in data:
                raise serializers.ValidationError(
                    {"password": "This field is required."}
                )
            if "email" not in data:
                raise serializers.ValidationError({"email": "This field is required."})
            if User.objects.filter(email=data["email"]).exists():
                raise serializers.ValidationError(
                    {"email": "A user with this email already exists."}
                )
            if len(data["password"]) < 8:
                raise serializers.ValidationError(
                    {
                        "password": "This password is too short. It must contain at least 8 characters."
                    }
                )
        return data

    def create(self, validated_data):
        email = validated_data.get("email", None)
        password = validated_data.get("password", None)

        if email is None and password is None:
            return User.objects.create_user(
                email=None, password=None, is_anonymous=True
            )
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
            )
            activation_link = self.context["request"].build_absolute_uri(
                f"/email/activate/{user.activation_token}"
            )
            self.send_confirmation_email(email, activation_link)
            return user

    @staticmethod
    def send_confirmation_email(user_email, activation_link):
        subject = "SplitFree - Account Activation"
        body = (
            "\n"
            "Welcome to SplitFree!\n\n"
            "Thank you for joining us. SplitFree is an open source organization that aims "
            "to provide an expense splitter app. Our application is free and devoid of any "
            "charges or advertisements.\n\n"
            f"Please click on the link below to confirm your sign up and activate your account:\n\n"
            f"{activation_link}\n\n"
            "If you didn't sign up for SplitFree, you can ignore this email.\n\n"
            "Best regards,\nThe SplitFree Team"
        )
        send_mail(subject, body, "your_sender_email@example.com", [user_email])


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, required=False
    )

    class Meta:
        model = Group
        fields = "__all__"

    def create(self, validated_data):
        user = self.context["request"].user

        group = Group(
            title=validated_data["title"],
            description=validated_data["description"]
            if "description" in validated_data
            else "",
            creator=user,
        )
        group.save()
        group.users.add(user)
        return group


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = "__all__"


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = "__all__"


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = "__all__"


class InviteTokenSerializer(serializers.Serializer):
    group = serializers.CharField()

    class Meta:
        model = InviteToken
        fields = ["group"]

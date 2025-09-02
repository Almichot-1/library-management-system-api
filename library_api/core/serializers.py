from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Book, Transaction


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_of_membership",
            "is_active_member",
            "is_active",
        ]
        read_only_fields = ["id", "is_active"]


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_date",
            "copies_total",
            "copies_available",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        copies_total = attrs.get("copies_total", getattr(self.instance, "copies_total", 0))
        copies_available = attrs.get("copies_available", getattr(self.instance, "copies_available", 0))
        if copies_available > copies_total:
            raise serializers.ValidationError("Copies available cannot exceed total copies.")
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = Transaction
        fields = ["id", "user", "book", "checkout_date", "return_date", "is_active"]
        read_only_fields = ["id", "checkout_date", "is_active"]


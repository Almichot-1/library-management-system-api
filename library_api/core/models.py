from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser with library-specific fields.
    """
    date_of_membership = models.DateField(default=timezone.now)
    is_active_member = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.username}"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField(null=True, blank=True)
    copies_total = models.PositiveIntegerField(default=1)
    copies_available = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["title", "author"]

    def clean(self):
        if self.copies_available > self.copies_total:
            raise ValidationError({
                "copies_available": "Copies available cannot exceed total copies."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="transactions")
    checkout_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-checkout_date"]
        constraints = [
            # Ensure only one active checkout per (user, book)
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=models.Q(return_date__isnull=True),
                name="uniq_active_checkout_per_user_book",
            )
        ]

    @property
    def is_active(self) -> bool:
        return self.return_date is None

    def __str__(self) -> str:
        status = "active" if self.is_active else "returned"
        return f"{self.user.username} → {self.book.title} ({status})"


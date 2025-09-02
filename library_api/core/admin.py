from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Book, Transaction


User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "date_of_membership", "is_active_member", "is_staff")
    list_filter = ("is_active_member", "is_staff", "is_superuser")
    search_fields = ("username", "email")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "published_date", "copies_total", "copies_available")
    search_fields = ("title", "author", "isbn")
    list_filter = ("published_date",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "checkout_date", "return_date", "is_active")
    list_filter = ("checkout_date", "return_date")
    search_fields = ("user__username", "book__title", "book__isbn")


from django.db import transaction as db_transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Book, Transaction
from .serializers import UserSerializer, BookSerializer, TransactionSerializer


User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_staff)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        # Only staff can create/update/delete other users
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me/transactions")
    def my_transactions(self, request):
        qs = Transaction.objects.filter(user=request.user).select_related("book").order_by("-checkout_date")
        serializer = TransactionSerializer(qs, many=True)
        return Response(serializer.data)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = {
        "copies_available": ["gt", "gte", "lt", "lte", "exact"],
    }
    search_fields = ["title", "author", "isbn"]

    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request):
        qs = self.get_queryset().filter(copies_available__gt=0)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.select_related("book", "user").all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        book_id = request.data.get("book")
        user = request.user
        if not book_id:
            return Response({"detail": "book is required"}, status=status.HTTP_400_BAD_REQUEST)

        book = get_object_or_404(Book, pk=book_id)
        if not user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        if not getattr(user, "is_active_member", True):
            return Response({"detail": "Inactive member"}, status=status.HTTP_403_FORBIDDEN)

        with db_transaction.atomic():
            book = Book.objects.select_for_update().get(pk=book.pk)
            if book.copies_available <= 0:
                return Response({"detail": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)
            # Ensure no active transaction exists for this user/book
            existing = Transaction.objects.filter(user=user, book=book, return_date__isnull=True).exists()
            if existing:
                return Response({"detail": "You already have this book checked out"}, status=status.HTTP_400_BAD_REQUEST)

            Transaction.objects.create(user=user, book=book)
            book.copies_available -= 1
            book.save(update_fields=["copies_available"])

        return Response({"detail": "Checked out successfully"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="return")
    def return_book(self, request):
        book_id = request.data.get("book")
        user = request.user
        if not book_id:
            return Response({"detail": "book is required"}, status=status.HTTP_400_BAD_REQUEST)

        book = get_object_or_404(Book, pk=book_id)

        with db_transaction.atomic():
            # Lock the book row
            book = Book.objects.select_for_update().get(pk=book.pk)
            tx = Transaction.objects.filter(user=user, book=book, return_date__isnull=True).first()
            if not tx:
                return Response({"detail": "No active checkout found for this book"}, status=status.HTTP_400_BAD_REQUEST)

            tx.return_date = timezone.now()
            tx.save(update_fields=["return_date"])
            book.copies_available = models.F("copies_available") + 1  # type: ignore
            book.save(update_fields=["copies_available"])
            # Refresh to resolve F expression
            book.refresh_from_db(fields=["copies_available"])

        return Response({"detail": "Returned successfully"}, status=status.HTTP_200_OK)


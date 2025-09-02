from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import User, Book, Transaction  # Import core.User instead of django.contrib.auth.models.User
from .serializers import UserSerializer, BookSerializer, TransactionSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # Use core.User
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(copies_available__gt=0)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'book_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                book = Book.objects.select_for_update().get(id=book_id)
                if book.copies_available <= 0:
                    return Response({'error': 'No copies available'}, status=status.HTTP_400_BAD_REQUEST)

                existing = Transaction.objects.filter(user=request.user, book=book, return_date__isnull=True)
                if existing.exists():
                    return Response({'error': 'You already have this book checked out'}, status=status.HTTP_400_BAD_REQUEST)

                book.copies_available -= 1
                book.save()

                trans = Transaction.objects.create(user=request.user, book=book)
                serializer = TransactionSerializer(trans)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        try:
            with transaction.atomic():
                trans = self.get_object()
                if trans.return_date:
                    return Response({'error': 'Book already returned'}, status=status.HTTP_400_BAD_REQUEST)

                trans.return_date = timezone.now()
                trans.save()

                book = trans.book
                book.copies_available += 1
                book.save()

                serializer = TransactionSerializer(trans)
                return Response(serializer.data)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
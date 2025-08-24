from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import User, Book, Transaction
from .serializers import UserSerializer, BookSerializer, TransactionSerializer
from django.db import transaction

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(id=self.request.user.id)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'author', 'isbn']
    filterset_fields = ['copies_available']

    @action(detail=False, methods=['get'])
    def available(self, request):
        queryset = self.get_queryset().filter(copies_available__gt=0)
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
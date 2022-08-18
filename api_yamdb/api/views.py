from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.filters import GenreCategoryFilter
from reviews.models import Category, Comment, Genre, Review, Title, User
from .mixins import ListCreateDestroyViewSet
from .permissions import (
    IsAdmin,
    IsAdminModeratorOwnerOrReadOnly,
    IsAdminOrReadOnly,
)
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    RegisterDataSerializer,
    ReviewSerializer,
    TitleGetSerializer,
    TitlePostSerializer,
    TokenSerializer,
    UserEditSerializer,
    UserSerializer,
)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)


def make_confirmation_code_and_sent_mail(recipient):
    confirmation_code = default_token_generator.make_token(recipient)
    send_mail(
        subject="Registration in YaMDb project",
        message=f"Ваш код подтверждения регистрации: {confirmation_code}",
        from_email=None,
        recipient_list=[recipient.email],
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterDataSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        make_confirmation_code_and_sent_mail(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    try:
        user = User.objects.get(
            username=serializer.data.get("username"),
            email=serializer.data.get("email"),
        )
        make_confirmation_code_and_sent_mail(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        pass
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def get_jwt_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, username=serializer.validated_data["username"]
    )

    if default_token_generator.check_token(
        user, serializer.validated_data["confirmation_code"]
    ):
        token = AccessToken.for_user(user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    lookup_field = "username"
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAdmin,)

    @action(
        methods=[
            "get",
            "patch",
        ],
        detail=False,
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=UserEditSerializer,
    )
    def users_own_profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "PATCH":
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = "slug"
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("name",)


class TitleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Title.objects.annotate(rating=Avg("reviews__score")).order_by(
            "id"
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TitleGetSerializer
        return TitlePostSerializer

    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = GenreCategoryFilter


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    pagination_class = PageNumberPagination
    permission_classes = [
        IsAdminModeratorOwnerOrReadOnly,
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        author = self.request.user
        serializer.save(author=author, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = PageNumberPagination
    permission_classes = [
        IsAdminModeratorOwnerOrReadOnly,
    ]

    def get_queryset(self):
        review_id = self.kwargs.get("review_id")
        title_id = self.kwargs.get("title_id")
        return Comment.objects.filter(
            review_id=review_id, review__title__id=title_id
        )

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        review = get_object_or_404(
            Review, id=self.kwargs.get("review_id"), title_id=title_id
        )
        serializer.save(author=self.request.user, review=review)

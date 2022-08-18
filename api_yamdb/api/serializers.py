from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title, User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")
        lookup_field = "slug"


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name", "slug")
        lookup_field = "slug"


class TitleSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault(),
    )
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        try:
            return round(obj.rating, 1)
        except TypeError:
            return None
        except AttributeError:
            pass

    class Meta:
        model = Title
        fields = (
            "id",
            "name",
            "year",
            "rating",
            "description",
            "genre",
            "category",
            "author",
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Title.objects.all(),
                fields=("name", "year", "category"),
                message="Вы уже создавали такое произведение.",
            )
        ]


class TitleGetSerializer(TitleSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)


class TitlePostSerializer(TitleSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field="slug", many=True, queryset=Genre.objects.all()
    )


class ReviewSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(
        slug_field="username",
        default=serializers.CurrentUserDefault(),
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "text",
            "author",
            "score",
            "pub_date",
        )

    def validate(self, data):
        title = get_object_or_404(
            Title, id=self.context.get("view").kwargs.get("title_id")
        )
        author = self.context["request"].user
        review_exists = Review.objects.filter(
            author=author, title=title
        ).exists()
        request_post = self.context["request"].method == "POST"
        if review_exists and request_post:
            raise serializers.ValidationError(
                "Вы уже оставляли отзыв на это произведение"
            )
        return data


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True,
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        fields = (
            "username",
            "email",
            "role",
            "bio",
            "first_name",
            "last_name",
        )
        model = User


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "username",
            "email",
            "role",
            "bio",
            "first_name",
            "last_name",
        )
        model = User
        read_only_fields = ("role",)


class RegisterDataSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError("Username 'me' is not correct!")
        return value

    class Meta:
        fields = ("username", "email")
        model = User


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class CommentSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(
        slug_field="username",
        default=serializers.CurrentUserDefault(),
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date")

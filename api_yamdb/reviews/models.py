import datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

CURRENT_YEAR = datetime.date.today().year


class User(AbstractUser):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    ROLES = [
        (ADMIN, "Administrator"),
        (MODERATOR, "Moderator"),
        (USER, "User"),
    ]
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        unique=True,
    )
    username = models.CharField(
        verbose_name="Имя пользователя", max_length=150, null=True, unique=True
    )
    role = models.CharField(
        verbose_name="Роль", max_length=50, choices=ROLES, default=USER
    )
    bio = models.TextField(verbose_name="О себе", null=True, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

        constraints = [
            models.CheckConstraint(
                check=~models.Q(username__iexact="me"),
                name="username_is_not_me",
            )
        ]

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return self.role == self.ADMIN


class Category(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    year = models.SmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(CURRENT_YEAR),
        ]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="titles",
    )
    genre = models.ManyToManyField(Genre, related_name="titles")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="titles",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    score = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ]
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        unique_together = (
            "title",
            "author",
        )
        ordering = ["id"]

    def __str__(self):
        return self.text


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text

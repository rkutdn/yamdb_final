from django_filters import rest_framework

from .models import Title


class GenreCategoryFilter(rest_framework.FilterSet):
    genre = rest_framework.CharFilter(field_name="genre__slug")
    category = rest_framework.CharFilter(field_name="category__slug")
    name = rest_framework.CharFilter(
        field_name="name", lookup_expr="icontains"
    )

    class Meta:
        fields = ("name", "year", "genre", "category")
        model = Title

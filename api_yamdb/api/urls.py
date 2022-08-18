from django.urls import include, path
from rest_framework import routers

from .views import (CategoryViewSet, CommentViewSet, GenreViewSet,
                    ReviewViewSet, TitleViewSet, UserViewSet, get_jwt_token,
                    register)

router = routers.DefaultRouter()
router.register("users", UserViewSet)
router.register("titles", TitleViewSet, basename="title")
router.register("categories", CategoryViewSet, basename="category")
router.register("genres", GenreViewSet, basename="genre")
router.register(
    r"titles/(?P<title_id>\d+)/reviews", ReviewViewSet, basename="review"
)
router.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    CommentViewSet,
    basename="comment",
)

v1_auth_url = [
    path("signup/", register, name="register"),
    path("token/", get_jwt_token, name="token"),
]

urlpatterns = [
    path("v1/", include(router.urls)),
    path("v1/auth/", include(v1_auth_url)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RadioViewSet, LanguageViewSet, CountryViewSet,
    GenreViewSet, VoteViewSet, RegionViewSet, CityViewSet
)

router = DefaultRouter()
router.register(r'radios', RadioViewSet)
router.register(r'languages', LanguageViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'cities', CityViewSet)
router.register(r'genres', GenreViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns += path(r'vote', VoteViewSet.as_view()),


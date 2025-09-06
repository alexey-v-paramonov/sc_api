from rest_framework import viewsets, permissions
from .models import Radio, Language, Country, Genre, Vote, Region, City
from .serializers import (
    RadioSerializer, LanguageSerializer, CountrySerializer,
    GenreSerializer, VoteSerializer, RegionSerializer, CitySerializer
)


class RadioViewSet(viewsets.ModelViewSet):
    queryset = Radio.objects.filter(enabled=True)
    serializer_class = RadioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer


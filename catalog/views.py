from rest_framework import viewsets, permissions, parsers
from rest_framework.response import Response
import json
from .models import Radio, Language, Country, Genre, Vote, Region, City
from .serializers import (
    RadioSerializer, LanguageSerializer, CountrySerializer,
    GenreSerializer, VoteSerializer, RegionSerializer, CitySerializer
)


class RadioViewSet(viewsets.ModelViewSet):
    queryset = Radio.objects.filter(enabled=True)
    serializer_class = RadioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'streams' in data and isinstance(data.get('streams'), str):
            try:
                data['streams'] = json.loads(data['streams'])
            except json.JSONDecodeError:
                return Response({'streams': ['Invalid JSON format.']}, status=400)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        if 'streams' in data and isinstance(data.get('streams'), str):
            try:
                data['streams'] = json.loads(data['streams'])
            except json.JSONDecodeError:
                return Response({'streams': ['Invalid JSON format.']}, status=400)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been used, we need to reload the instance
            # from the database to get the updated data.
            instance = self.get_object()
            serializer = self.get_serializer(instance)

        return Response(serializer.data)


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.order_by('name_eng')
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
    queryset = Region.objects.order_by('name_eng')
    serializer_class = RegionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        country_id = self.request.query_params.get('country_id')
        if country_id:
            queryset = queryset.filter(country_id=country_id)
        return queryset


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.order_by('name_eng')
    serializer_class = CitySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        country_id = self.request.query_params.get('country_id')
        region_id = self.request.query_params.get('region_id')
        if country_id:
            queryset = queryset.filter(country_id=country_id)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        return queryset


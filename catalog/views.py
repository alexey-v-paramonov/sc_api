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
    # lookup_field = 'slug'
    # parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def _normalize_data(self, request):
        
        request_data = request.data
        data = request_data.copy()
        if 'genres' in request_data:
            data['genres'] = request_data.getlist('genres')
        if 'language' in request_data:
            data['languages'] = request_data.getlist('language')        
            data.pop('language', None)

        # Normalize 'streams'
        if 'streams' in data:
            streams_data = data['streams']
            if isinstance(streams_data, str):
                print("Streams is a string, attempting to parse as JSON")
                try:
                    streams_data = json.loads(streams_data)
                except json.JSONDecodeError:
                    # Let the serializer handle the invalid format error
                    pass
            
            # Handle potential nesting from form parsers
            if isinstance(streams_data, list) and len(streams_data) > 0 and isinstance(streams_data[0], list):
                print("Streams is a list of lists, flattening")
                streams_data = streams_data[0]
            
            data['streams'] = streams_data
        if 'region' in data and data['region'] == 'null':
            data['region'] = None

        # # You can add similar normalization for 'genres' and 'language' if they also face issues
        # # For example:
        # if 'genres' in data and isinstance(data['genres'], list) and len(data['genres']) == 1:
        #     if isinstance(data['genres'][0], str) and ',' in data['genres'][0]:
        #         data.setlist('genres', data['genres'][0].split(','))
        data['user'] = request.user.id
        return data.dict()

    def create(self, request, *args, **kwargs):
        data = self._normalize_data(request)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = self._normalize_data(request)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

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


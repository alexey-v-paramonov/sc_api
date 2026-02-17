from django.utils import timezone
from django.db.models import Q, Prefetch

from rest_framework.views import APIView

from rest_framework import viewsets, permissions, parsers
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
import json
from .models import Radio, Language, Country, Genre, Vote, Region, City, Stream
from .serializers import (
    RadioSerializer, LanguageSerializer, CountrySerializer,
    GenreSerializer, VoteSerializer, RegionSerializer, CitySerializer,
    PublicRadioSerializer
)


class RadioViewSet(viewsets.ModelViewSet):
    queryset = Radio.objects.all()
    serializer_class = RadioSerializer
    permission_classes = [permissions.IsAuthenticated]
    # lookup_field = 'slug'
    # parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Radio.objects.filter(user=user)
        return Radio.objects.none()

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
    permission_classes = [permissions.IsAuthenticated]


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.order_by('name_eng')
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticated]


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticated]


class VoteViewSet(APIView):
    
    permission_classes = (permissions.AllowAny, )
    
    def post(self, request):
        radio_id = request.data.get('radio_id')
        if not radio_id:
            return Response({"error": "radio_not_set"}, status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        if not ip:
            return Response({"error": "ip_undefined"}, status=400)

        score = request.data.get('score')
        if score is None:
            return Response({"error": "score_not_set"}, status=400)
        
        try:
            radio = Radio.objects.get(id=radio_id)
        except Radio.DoesNotExist:
            return Response({"error": "radio_not_found"}, status=400)

        # Delete Vote object older than 1 hour
        Vote.objects.filter(created__lt=timezone.now()-timezone.timedelta(hours=1)).delete()
        if Vote.objects.filter(radio=radio, ip=ip).exists():
            return Response({"error": "vote_exists"}, status=403)
            
        Vote.objects.create(
            radio=radio,
            ip=ip,
        )
        
        radio.total_votes += 1
        radio.total_score += int(score)
        radio.save(update_fields=['total_votes', 'total_score'])
        return Response({}, status=201)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.order_by('name_eng')
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated]

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


class CatalogPagination(PageNumberPagination):
    """Custom pagination for public catalog"""
    page_size = 30
    page_size_query_param = 'per_page'
    max_page_size = 100


class PublicRadioCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API endpoint for radio catalog.
    Does not require authentication.
    Supports filtering, searching, sorting, and pagination.
    """
    serializer_class = PublicRadioSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CatalogPagination

    def get_queryset(self):
        """
        Build queryset with filtering, searching, and sorting
        """
        queryset = Radio.objects.filter(enabled=True).select_related(
            'country', 'region', 'city'
        ).prefetch_related(
            'genres', 'languages', 
            Prefetch('streams', queryset=Stream.objects.filter(enabled=True))
        )

        # Get query parameters
        search = self.request.query_params.get('search', '').strip()
        genre = self.request.query_params.get('genre', '').strip()
        country = self.request.query_params.get('country', '').strip()
        region = self.request.query_params.get('region', '').strip()
        city = self.request.query_params.get('city', '').strip()
        language = self.request.query_params.get('language', '').strip()
        sort = self.request.query_params.get('sort', 'rating').strip()

        # Apply search filter (minimum 3 characters)
        if search and len(search) >= 3:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(genres__name_eng__icontains=search) |
                Q(genres__name__icontains=search) |
                Q(country__name_eng__icontains=search) |
                Q(country__name__icontains=search) |
                Q(city__name_eng__icontains=search) |
                Q(city__name__icontains=search)
            ).distinct()

        # Apply filters
        if genre:
            queryset = queryset.filter(
                Q(genres__name_eng__iexact=genre) | Q(genres__name__iexact=genre)
            )
        
        if country:
            queryset = queryset.filter(
                Q(country__name_eng__iexact=country) | Q(country__name__iexact=country)
            )
        
        if region:
            queryset = queryset.filter(
                Q(region__name_eng__iexact=region) | Q(region__name__iexact=region)
            )
        
        if city:
            queryset = queryset.filter(
                Q(city__name_eng__iexact=city) | Q(city__name__iexact=city)
            )
        
        if language:
            queryset = queryset.filter(
                Q(languages__name_eng__iexact=language) | Q(languages__name__iexact=language)
            )

        # Apply sorting
        if sort == 'votes':
            queryset = queryset.order_by('-total_votes')
        elif sort == 'created':
            queryset = queryset.order_by('-created')
        else:  # default to rating
            # Sort by rating calculation: total_score / total_votes (handle division by zero)
            queryset = queryset.extra(
                select={'rating_calc': 'CASE WHEN total_votes > 0 THEN CAST(total_score AS FLOAT) / total_votes ELSE 0 END'}
            ).order_by('-rating_calc')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to add filters in response
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
            
            # Add filters to response
            filters = self._get_available_filters(queryset)
            response_data.data['filters'] = filters
            
            return response_data

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total': queryset.count(),
            'results': serializer.data,
            'filters': self._get_available_filters(queryset)
        })

    def _get_available_filters(self, queryset):
        """
        Get available filter options based on current queryset
        """
        # Get lang parameter to determine which field to use
        lang = self.request.query_params.get('lang', '').strip()
        name_field = 'name' if lang == 'ru' else 'name_eng'
        
        # Get distinct values for each filter
        genres = Genre.objects.filter(
            radios__in=queryset
        ).distinct().values_list(name_field, flat=True)
        
        countries = Country.objects.filter(
            radios__in=queryset
        ).distinct().values_list(name_field, flat=True)
        
        regions = Region.objects.filter(
            radios__in=queryset
        ).exclude(**{f'{name_field}__isnull': True}).distinct().values_list(name_field, flat=True)
        
        cities = City.objects.filter(
            radios__in=queryset
        ).exclude(**{f'{name_field}__isnull': True}).distinct().values_list(name_field, flat=True)
        
        languages = Language.objects.filter(
            radios__in=queryset
        ).distinct().values_list(name_field, flat=True)

        return {
            'genres': sorted([g for g in genres if g]),
            'countries': sorted([c for c in countries if c]),
            'regions': sorted([r for r in regions if r]),
            'cities': sorted([c for c in cities if c]),
            'languages': sorted([lang for lang in languages if lang])
        }

    def get_paginated_response(self, data):
        """
        Customize paginated response format
        """
        return Response({
            'total': self.paginator.page.paginator.count,
            'total_pages': self.paginator.page.paginator.num_pages,
            'current_page': self.paginator.page.number,
            'per_page': self.paginator.page_size,
            'results': data,
        })


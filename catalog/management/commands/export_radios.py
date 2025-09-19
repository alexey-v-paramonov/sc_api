import json

from django.core.management.base import BaseCommand
from catalog.models import Radio
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, ExpressionWrapper, FloatField, Case, When, Value

class Command(BaseCommand):
    help = 'Export all Radio models with related Stream, Country, Region, City, Genre to a JSON file.'

    def handle(self, *args, **options):
        radios = Radio.objects.select_related(
            'country', 'region', 'city', 'user'
        ).prefetch_related(
            'genres', 'languages', 'streams'
        ).filter(enabled=True)
        radios = radios.annotate(
            rating=Case(
                When(total_votes=0, then=Value(None, output_field=FloatField())),
                When(total_score=0, then=Value(None, output_field=FloatField())),
                default=ExpressionWrapper(
                    F('total_score') * 1.0 / F('total_votes'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).order_by('-rating', 'name')
        data = []
        for radio in radios:
            data.append({
                'id': radio.id,
                'name': radio.name,
                'slug': radio.slug,
                'description': radio.description,
                'enabled': radio.enabled,
                'website_url': radio.website_url,
                'logo': radio.logo.url if radio.logo else None,
                'country': {
                    'id': radio.country.id,
                    'iso2': radio.country.iso2,
                    'name': radio.country.name,
                    'name_eng': radio.country.name_eng,
                } if radio.country else None,
                'region': {
                    'id': radio.region.id,
                    'name': radio.region.name,
                    'name_eng': radio.region.name_eng,
                } if radio.region else None,
                'city': {
                    'id': radio.city.id,
                    'name': radio.city.name,
                    'name_eng': radio.city.name_eng,
                } if radio.city else None,
                'genres': [
                    {'id': genre.id, 'name': genre.name, 'name_eng': genre.name_eng}
                    for genre in radio.genres.all()
                ],
                'languages': [
                    {'id': lang.id, 'name': lang.name, 'name_eng': lang.name_eng}
                    for lang in radio.languages.all()
                ],
                'streams': [
                    {
                        'id': stream.id,
                        'stream_url': stream.stream_url,
                        'audio_format': stream.audio_format,
                        'bitrate': stream.bitrate,
                        'server_type': stream.server_type,
                    }
                    for stream in radio.streams.filter(enabled=True).order_by('-bitrate')
                ],
                'total_votes': radio.total_votes,
                'total_score': radio.total_score,
                'user_id': radio.user.id,
                'rating': radio.rating,
            })
        with open('exported_radios.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f'Exported {len(data)} radios to exported_radios.json'))

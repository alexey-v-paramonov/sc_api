import json
import os

from django.core.management.base import BaseCommand

from catalog.models import Radio
from users.models import Language as UserLanguage


class Command(BaseCommand):
    help = 'Export catalog filter options (genres, countries, regions, cities, languages) into JSON files per owner language (eng/ru)'

    def handle(self, *args, **options):
        # Prepare containers for english and russian
        out = {
            'eng': {
                'genres': set(),
                'countries': set(),
                'regions': set(),
                'cities': set(),
                'languages': set(),
            },
            'ru': {
                'genres': set(),
                'countries': set(),
                'regions': set(),
                'cities': set(),
                'languages': set(),
            }
        }

        radios = Radio.objects.select_related('country', 'region', 'city', 'user').prefetch_related('genres', 'languages')

        for radio in radios:
            user = getattr(radio, 'user', None)
            if not user:
                continue

            # Determine target language bucket based on owner preference
            if getattr(user, 'language', None) == UserLanguage.ENG:
                bucket = 'eng'
            elif getattr(user, 'language', None) == UserLanguage.RU:
                bucket = 'ru'
            else:
                # skip other preferences
                continue

            # Genres
            for g in radio.genres.all():
                name = g.name_eng if bucket == 'eng' and g.name_eng else g.name
                if name:
                    out[bucket]['genres'].add(name)

            # Country
            c = radio.country
            if c:
                name = c.name_eng if bucket == 'eng' and c.name_eng else c.name
                if name:
                    out[bucket]['countries'].add(name)

            # Region
            r = radio.region
            if r:
                name = r.name_eng if bucket == 'eng' and r.name_eng else r.name
                if name:
                    out[bucket]['regions'].add(name)

            # City
            ci = radio.city
            if ci:
                name = ci.name_eng if bucket == 'eng' and ci.name_eng else ci.name
                if name:
                    out[bucket]['cities'].add(name)

            # Languages (radio.languages is a M2M to catalog Language model)
            for lang in radio.languages.all():
                name = lang.name_eng if bucket == 'eng' and lang.name_eng else lang.name
                if name:
                    out[bucket]['languages'].add(name)

        # Ensure output directory is current working directory
        cwd = os.getcwd()

        for bucket_key, buckets in out.items():
            suffix = 'eng' if bucket_key == 'eng' else 'ru'
            for filter_name, values in buckets.items():
                filename = f"{filter_name}_{suffix}.json"
                path = os.path.join(cwd, filename)
                data = sorted(values)
                try:
                    with open(path, 'w', encoding='utf-8') as fh:
                        json.dump(data, fh, ensure_ascii=False, indent=2)
                    self.stdout.write(self.style.SUCCESS(f"Wrote {path} ({len(data)} items)"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to write {path}: {e}"))

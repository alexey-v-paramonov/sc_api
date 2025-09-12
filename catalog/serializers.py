
from rest_framework import serializers
import requests
from requests.exceptions import RequestException
from .models import Radio, Language, Country, Genre, Stream, Vote, Region, City


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'



class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class StreamSerializer(serializers.ModelSerializer):

    def validate_stream_url(self, value):
        """
        Validates that the stream URL is a connectable audio stream.
        """
        print("Checking:", value)        
        if not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError("url_invalid")

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Icy-MetaData': '1'  # Request metadata from Shoutcast/Icecast servers
        }

        try:
            # Use stream=True to avoid downloading the entire file
            response = requests.get(value, timeout=5, headers=headers, stream=True)
            response.raise_for_status()  # Check for HTTP errors like 404 or 500

            # server_type = self.initial_data.get('server_type', '').lower()
            # if server_type == 'icecast':
            #     # Read the first few bytes of the stream to check for "icecast"
            #     first_chunk = next(response.iter_content(chunk_size=512), b'')
            #     if b'icecast' in first_chunk.lower():
            #         return value

            # Check if Content-Type header indicates an audio stream
            content_type = response.headers.get('Content-Type', '').lower()
            if 'audio' not in content_type:
                raise serializers.ValidationError("content_type_not_audio")


        except RequestException:
            # Catches connection errors, timeouts, DNS errors, etc.
            raise serializers.ValidationError("connection_error")

        return value
        
    class Meta:
        model = Stream
        fields = ['id', 'stream_url', 'audio_format', 'bitrate', 'server_type']
        read_only_fields = ['id']


class RadioSerializer(serializers.ModelSerializer):
    streams = StreamSerializer(many=True)

    class Meta:
        model = Radio
        fields = [
            'id', 'name', 'slug', 'description', 'enabled', 'website_url', 'logo',
            'languages', 'country', 'region', 'city', 'genres', 'streams',
            'total_votes', 'average_rating', 'user'
        ]
        read_only_fields = ['id', 'slug', 'enabled', 'total_votes', 'average_rating']

    def __init__(self, *args, **kwargs):
        # Call the superclass's __init__ first
        super().__init__(*args, **kwargs)

        # If an instance is being updated, the 'logo' field is not required.
        if self.instance:
            self.fields['logo'].required = False

    def create(self, validated_data):
        streams_data = validated_data.pop('streams')
        languages_data = validated_data.pop('languages', None)
        genres_data = validated_data.pop('genres', None)
        
        radio = Radio.objects.create(**validated_data)

        if languages_data:
            radio.languages.set(languages_data)
        if genres_data:
            radio.genres.set(genres_data)

        for stream_data in streams_data:
            Stream.objects.create(radio=radio, **stream_data)
        return radio

    def validate_website_url(self, value):
        if not value:
            return value  # Don't validate if the URL is empty

        if not (value.startswith('http://') or value.startswith('https://')):
            raise serializers.ValidationError("url_invalid")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        try:
            # Use HEAD request to be efficient and not download the whole page
            response = requests.head(value, timeout=5, headers=headers, allow_redirects=True)

            # Check for a successful status code (e.g., 200 OK)
            response.raise_for_status()

            # Check if the Content-Type header indicates an HTML document
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                raise serializers.ValidationError("content_type")

        except RequestException as e:
            # This will catch connection errors, timeouts, invalid URLs, etc.
            raise serializers.ValidationError("connection_error")

        return value

    def update(self, instance, validated_data):
        streams_data = validated_data.pop('streams', None)
        languages_data = validated_data.pop('languages', None)
        genres_data = validated_data.pop('genres', None)
        
        instance = super().update(instance, validated_data)

        if languages_data is not None:
            instance.languages.set(languages_data)
        if genres_data is not None:
            instance.genres.set(genres_data)

        if streams_data is not None:
            instance.streams.all().delete()
            for stream_data in streams_data:
                Stream.objects.create(radio=instance, **stream_data)
        return instance


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'radio', 'rating']
        read_only_fields = ['id']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        radio = validated_data['radio']
        rating = validated_data['rating']

        vote, created = Vote.objects.update_or_create(
            user=user, radio=radio,
            defaults={'rating': rating}
        )
        return vote

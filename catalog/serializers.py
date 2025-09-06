
from rest_framework import serializers
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
    class Meta:
        model = Stream
        fields = ['id', 'url', 'audio_format', 'bitrate']


class RadioSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)
    country = CountrySerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    streams = StreamSerializer(many=True)

    class Meta:
        model = Radio
        fields = [
            'id', 'name', 'description', 'enabled', 'website_url', 'logo',
            'languages', 'country', 'region', 'city', 'genres', 'streams',
            'total_votes', 'average_rating'
        ]
        read_only_fields = ['total_votes', 'average_rating']

    def create(self, validated_data):
        streams_data = validated_data.pop('streams')
        radio = Radio.objects.create(**validated_data)
        for stream_data in streams_data:
            Stream.objects.create(radio=radio, **stream_data)
        return radio

    def update(self, instance, validated_data):
        streams_data = validated_data.pop('streams', None)
        instance = super().update(instance, validated_data)

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

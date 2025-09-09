
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.contrib.auth import get_user_model

User = get_user_model()

def validate_logo_image(image):
    """
    Validator for the radio logo.
    Checks if the image is square and has a minimum size of 256x256 pixels.
    """
    try:
        width, height = get_image_dimensions(image)
        if width != height:
            raise ValidationError("The logo must be a square image.")
        if width < 256:
            raise ValidationError("The minimum size for the logo is 256x256 pixels.")
    except (TypeError, AttributeError):
        raise ValidationError("Invalid image file.")


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_eng = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=64, unique=True)
    name_eng = models.CharField(max_length=64, unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_eng = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name



class Region(models.Model):
    name = models.CharField(max_length=128)
    name_eng = models.CharField(max_length=128, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=128)
    name_eng = models.CharField(max_length=128, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.name


class Radio(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    website_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='app_radio_logos/', validators=[validate_logo_image])
    languages = models.ManyToManyField(Language, related_name='radios')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='radios')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='radios', null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='radios', null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name='radios')
    total_votes = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)

    user = models.ForeignKey(
        User,
        verbose_name="Owner",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )


    def __str__(self):
        return self.name

    def update_rating(self):
        """
        Recalculates the average rating and total votes for the radio.
        """
        votes = self.votes.all()
        self.total_votes = votes.count()
        if self.total_votes > 0:
            self.average_rating = sum(vote.rating for vote in votes) / self.total_votes
        else:
            self.average_rating = 0.0
        self.save(update_fields=['total_votes', 'average_rating'])


class Stream(models.Model):
    AUDIO_FORMAT_CHOICES = [
        ('mp3', 'MP3'),
        ('aac', 'AAC'),
        ('flac', 'FLAC'),
        ('opus', 'Opus'),
        ('ogg', 'OGG'),
        ('other', 'Other'),
    ]
    radio = models.ForeignKey(Radio, on_delete=models.CASCADE, related_name='streams')
    url = models.URLField()
    audio_format = models.CharField(max_length=10, choices=AUDIO_FORMAT_CHOICES)
    bitrate = models.PositiveIntegerField(help_text="in kbps")

    def __str__(self):
        return f"{self.radio.name} - {self.get_audio_format_display()} ({self.bitrate} kbps)"


class Vote(models.Model):
    radio = models.ForeignKey(Radio, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    rating = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('radio', 'user')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.radio.update_rating()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.radio.update_rating()


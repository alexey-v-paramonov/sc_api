
from django.db import models
from slugify import slugify
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.contrib.auth import get_user_model
from mobile_application.models import ServerType
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

User = get_user_model()

def validate_logo_image(image):
    """
    Validator for the radio logo.
    Checks if the image is square and has a minimum size of 250x250 pixels.
    """
    try:
        width, height = get_image_dimensions(image)
        if width != height:
            raise ValidationError("The logo must be a square image.")
        if width < 250:
            raise ValidationError("The minimum size for the logo is 250x250 pixels.")
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
    region = models.ForeignKey(Region, null=True, on_delete=models.CASCADE, related_name='cities')
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.name


class Radio(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    website_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='catalog_logos/', validators=[validate_logo_image])
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

    def _generate_unique_slug(self):
        base_slug = slugify(self.name) if self.name else "radio"
        slug = base_slug
        counter = 1
        while Radio.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()

        # Resize logo if needed
        if self.logo:
            try:
                self.logo.open()
                img = Image.open(self.logo)
                width, height = img.size
                if width > 512 or height > 512:
                    img = img.resize((512, 512), Image.LANCZOS)
                    buffer = BytesIO()
                    img_format = img.format if img.format else 'PNG'
                    img.save(buffer, format=img_format)
                    buffer.seek(0)
                    file_name = self.logo.name.split('/')[-1]
                    self.logo.save(file_name, ContentFile(buffer.read()), save=False)
            except Exception:
                pass  # If resizing fails, save original

        super().save(*args, **kwargs)

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
    stream_url = models.URLField()
    audio_format = models.CharField(max_length=10, choices=AUDIO_FORMAT_CHOICES)
    bitrate = models.PositiveIntegerField(help_text="in kbps")
    server_type = models.CharField(
        "Server type",
        max_length=20,
        choices=ServerType.choices,
        blank=False,
        null=False,
        default=ServerType.SHOUTCAST,
    )

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


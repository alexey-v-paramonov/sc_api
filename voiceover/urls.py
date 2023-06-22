from django.urls import path

from voiceover.views import VoiceoverAPI
urlpatterns = path(r'voiceover/', VoiceoverAPI.as_view()),


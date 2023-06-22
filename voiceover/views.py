from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from speechkit import Session
from speechkit import SpeechSynthesis


class VoiceoverAPI(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request, format=None):

        text = request.data.get("text")
        lang = request.data.get("lang")

        if not text:
            return Response({"text": "required"}, status=status.HTTP_400_BAD_REQUEST)

        if not lang:
            return Response({"lang": "required"}, status=status.HTTP_400_BAD_REQUEST)
        
        voice = request.data.get("voice", "filipp")
        speed = request.data.get("speed", "1")

        session = Session.from_api_key(settings.SPEECHKIT_API_KEY, settings.SPEECHKIT_FOLDER_ID)
        synthesizeAudio = SpeechSynthesis(session)

        synthesizeAudio.synthesize(
            'news.wav',
            text=text,
            lang=lang,
            voice=voice,
            format='lpcm',
            speed=speed,
            sampleRateHertz='48000'
        )


        return Response({})



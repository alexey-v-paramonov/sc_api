import subprocess
import base64

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from speechkit import Session
from speechkit import SpeechSynthesis
from ipware import get_client_ip



class VoiceoverAPI(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request, format=None):

        client_ip = get_client_ip()

        if client_ip is None:
            return Response(
                {"auth": "failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        text = request.data.get("text")
        lang = request.data.get("lang")

        if not text:
            return Response({"text": "required"}, status=status.HTTP_400_BAD_REQUEST)

        if not lang:
            return Response({"lang": "required"}, status=status.HTTP_400_BAD_REQUEST)
        
        voice = request.data.get("voice", "filipp")
        speed = request.data.get("speed", "1")
        emotion = request.data.get("emotion", "neutral")

        session = Session.from_api_key(settings.SPEECHKIT_API_KEY, settings.SPEECHKIT_FOLDER_ID)
        synthesizeAudio = SpeechSynthesis(session)

        pcm_buff = synthesizeAudio.synthesize_stream(
            text=text,
            lang=lang,
            voice=voice,
            format='lpcm',
            speed=speed,
            emotion=emotion,
            sampleRateHertz='48000'
        )
        process=subprocess.Popen(
            ["lame",
             "-r",
             "-s", "22.05",
             "-b", "320",
             "-q", "0",
             "-S", # Silent
             "-",
             "-"
             ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        lame_output = process.communicate(input=pcm_buff)[0]
        base64_audio = f"data:audio/mpeg;base64,{base64.b64encode(lame_output)}" 

        return Response({
            "format": "mp3",
            "bitrate": "320",
            "audio": base64_audio
        })



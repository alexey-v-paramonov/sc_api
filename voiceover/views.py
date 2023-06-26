import subprocess
import base64

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from speechkit import Session
from speechkit import SpeechSynthesis
from ipware import get_client_ip

from radiotochka.billing import BillingError, RTBilling
from radio.models import RadioServer


class VoiceoverAPI(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request, format=None):

        client_ip = get_client_ip()
        failed_auth_response = Response(
            {"auth": "failed"},
            status=status.HTTP_400_BAD_REQUEST
        )
        if client_ip is None:
            return failed_auth_response
            
        billing_type = request.data.get("billing", "").lower().strip()
        if not billing_type in ["shared", "standalone"]:
            return failed_auth_response

        text = request.data.get("text")
        billing = RTBilling()
        price = RTBilling.SPEECHKIT_PRICE_PER_SYMBOL * len(text)
        if billing_type == "shared":
            username = request.data.get("username", "").lower().strip()
            if not username:
                return failed_auth_response

            is_known_instance = RadioServer.objects.filter(ip=client_ip).exists()
            if not is_known_instance:
                return failed_auth_response

            try:
                user_id = billing.get_user_id_by_login(username)
            except BillingError:
                return failed_auth_response
        elif billing_type == "standalone":
            try:
                user_id = billing.get_user_id_by_ip(client_ip)
            except BillingError:
                return failed_auth_response

        else:
            return failed_auth_response

        try:
            balance = billing.get_user_balance(user_id)
        except BillingError:
            return failed_auth_response

        if balance <= price:
            return Response(
                {"balance": "insufficient"},
                status=status.HTTP_400_BAD_REQUEST
            )

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
             "-s", "48",
             "--signed",
             "--little-endian",
             "-m", "m",
             "-b", "320",
             "-q", "0",
             "-S", # Silent
             "-",
             "-"
             ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        lame_output = process.communicate(input=pcm_buff)[0]
        base64_audio = f"data:audio/mpeg;base64,{base64.b64encode(lame_output)}" 
        billing.update_client_balance(user_id, balance - price)

        return Response({
            "format": "mp3",
            "bitrate": "320",
            "audio": base64_audio
        })



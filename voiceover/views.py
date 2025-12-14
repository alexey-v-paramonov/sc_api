import logging
from decimal import Decimal

import subprocess
import base64

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from speechkit import Session
from speechkit import SpeechSynthesis
from ipware import get_client_ip
from django.utils import timezone

from radio.models import RadioServer, HostedRadio, SelfHostedRadio
from payments.models import ChargedServiceType, Charge

logger = logging.getLogger('tts')


class VoiceoverAPI(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request, format=None):

        client_ip, _ = get_client_ip(request)
        logger.info("##### New TTS request from %s, time: %s", client_ip, timezone.now())
        failed_auth_response = Response(
            {"auth": "failed"},
            status=status.HTTP_400_BAD_REQUEST
        )
        if client_ip is None:
            return failed_auth_response
            
        billing_type = request.data.get("billing", "").lower().strip()
        logger.info("TTS %s: billing type: %s", client_ip, billing_type)

        if not billing_type in ["shared", "standalone"]:
            return failed_auth_response

        text = request.data.get("text")
        logger.info("TTS %s: text: %s", client_ip, text)

        if not text:
            return Response({"text": "required"}, status=status.HTTP_400_BAD_REQUEST)


        if billing_type == "shared":
            username = request.data.get("username", "").lower().strip()
            logger.info("TTS %s: billing: %s, username: %s", client_ip, billing_type, username)
            if not username:
                return failed_auth_response

            is_known_instance = RadioServer.objects.filter(ip=client_ip).exists()
            if not is_known_instance:
                return failed_auth_response

            try:
                radio = HostedRadio.objects.get(login=username)
            except HostedRadio.DoesNotExist:
                return failed_auth_response
        elif billing_type == "standalone":
            try:
                radio = SelfHostedRadio.objects.get(ip=client_ip)
            except SelfHostedRadio.DoesNotExist:
                return failed_auth_response
            logger.info("TTS %s: billing: %s, Radio ID: %s", client_ip, billing_type, radio.id)
        else:
            return failed_auth_response

        balance = radio.user.balance
        price = Decimal((settings.SPEECHKIT_PRICE_PER_SYMBOL_RUB if radio.user.is_rub() else settings.SPEECHKIT_PRICE_PER_SYMBOL_USD)  * len(text))

        logger.info("TTS %s: radio ID: %s, balance: %s, price: %s", client_ip, radio.id, balance, price)

        if balance <= price:
            return Response(
                {"balance": "insufficient"},
                status=status.HTTP_400_BAD_REQUEST
            )

        lang = request.data.get("lang")

        if not lang:
            return Response({"lang": "required"}, status=status.HTTP_400_BAD_REQUEST)
        
        voice = request.data.get("voice", "filipp")
        speed = request.data.get("speed", "1")
        emotion = request.data.get("emotion", "neutral")
        logger.info("TTS %s: radio ID: %s, lang: %s, voice: %s, speed: %s, emotion: %s", client_ip, radio.id, lang, voice, speed, emotion)

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
        base64_audio = f"data:audio/mpeg;base64,{base64.b64encode(lame_output).decode('utf-8')}"
        radio.user.balance = balance - price
        radio.user.save()
        Charge.objects.create(
            user=radio.user,
            service_type=ChargedServiceType.VOICEOVER,
            description=str(len(text)), 
            price=price,
            currency=radio.user.currency
        )

        return Response({
            "format": "mp3",
            "bitrate": "320",
            "audio": base64_audio
        })



import socket
import paramiko
import ipaddress

from rest_framework import serializers
from radio.models import SelfHostedRadio, HostedRadio, RadioServer
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)
from django.conf import settings
from django.db.models import Sum


class RadioServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = RadioServer
        exclude = ()


class HostedRadioSerializer(CustomErrorMessagesModelSerializer):

    # server = RadioServerSerializer(read_only=True)
    server_data = RadioServerSerializer(source='server', read_only=True)
    
    def to_internal_value(self, data):
        data['server'] = RadioServer.objects.filter(available=True).first().id
        data['login'] = data['login'].lower()
        
        return super().to_internal_value(data)

    def validate_login(self, login):
        if login.isdigit() or not login[0].isalpha():
            raise serializers.ValidationError("regex")

        return login
        
    def validate_is_demo(self, is_demo):
        if HostedRadio.objects.filter(user=self.context['request'].user, is_demo=True).exists():
            raise serializers.ValidationError("demo_exists")

        return is_demo

    class Meta:
        model = HostedRadio
        fields = (
            'comment',
            'debug_msg',
            'domain',
            'id',
            'initial_audio_format',
            'initial_bitrate',
            'initial_du',
            'initial_listeners',
            'is_blocked',
            'is_demo',
            'login',
            'name',
            'server',
            'status',
            'ts_created',
            'user',
            'price',
            'copyright_type',
            'server_data'
        )
        extra_kwargs = {"price": {"read_only": True}}


class SelfHostedRadioSerializer(CustomErrorMessagesModelSerializer):

    # price = serializers.SerializerMethodField()


    def validate(self, data):

        ip = data['ip']
        ssh_username = data.get('ssh_username', None)
        ssh_password = data.get('ssh_password', None)
        ssh_port = data.get('ssh_port', None)
        domain = data.get('domain', None)
        
        try:
            ip = ipaddress.ip_address(ip)
            if ip.is_loopback:
                raise serializers.ValidationError({"ip": "invalid_ip"})
        except ValueError:
            raise serializers.ValidationError({"ip": "invalid_ip"})

        if domain:

            # Check if domain resolves to the IP specified
            try:
                domain_ip = socket.gethostbyname(domain)
            except:
                raise serializers.ValidationError(
                    {"domain": "wrong_ip_resolved"})

            if domain_ip != ip:
                raise serializers.ValidationError({"domain": "wrong_ip"})

        # Check SSH port connection
        if ssh_username and ssh_password and ssh_port:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)

            try:
                s.connect((ip, int(ssh_port)))
            except Exception:
                raise serializers.ValidationError(
                    {"ip": "ssh_port_connection_failed"})
            finally:
                s.shutdown(socket.SHUT_RDWR)
                s.close()

            # Check SSH credentials
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(ip, ssh_username, ssh_password, ssh_port)
                ssh.connect(ip, username=ssh_username, password=ssh_password,
                            port=ssh_port, allow_agent=False, look_for_keys=False)
            except Exception:
                ssh.close()
                raise serializers.ValidationError(
                    {"ip": "ssh_connection_failed"})

            _, stdout, _ = ssh.exec_command(
                'cat /etc/system-release /etc/issue 2>/dev/null')
            ssh_output = stdout.read().lower().decode("utf-8")
            ssh.close()

            if ssh_output.find("centos") == -1 and ssh_output.find("ubuntu") == -1:
                raise serializers.ValidationError({"ip": "wrong_os"})

        return data

    class Meta:
        model = SelfHostedRadio
        fields = (
            'comment',
            'debug_msg',
            'domain',
            'id',
            'is_blocked',
            'name',
            'status',
            'ts_created',
            'is_trial_period',
            'trial_period_hours_left',
            'user',
            'price',
            'ip',
            'ssh_username',
            'ssh_password',
            'ssh_port',
            'custom_price',
            'is_unbranded'
        )
        extra_kwargs = {
            "price": {"read_only": True},
            "custom_price": {"read_only": True},
        }

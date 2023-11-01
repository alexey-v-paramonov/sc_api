import socket
import paramiko

from rest_framework import serializers
from radio.models import SelfHostedRadio, HostedRadio, RadioServer
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)

class RadioServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = RadioServer
        exclude = ()


class HostedRadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = HostedRadio
        exclude = ()

class SelfHostedRadioSerializer(CustomErrorMessagesModelSerializer):

    def validate(self, data):

        ip = data['ip']
        ssh_username  = data.get('ssh_username', None)
        ssh_password = data.get('ssh_password', None)
        ssh_port = data.get('ssh_port', None)
        domain = data.get('domain', None)
        if domain:

            # Check if domain resolves to the IP specified
            try:
                domain_ip = socket.gethostbyname(domain)
            except:
                raise serializers.ValidationError({"domain": "wrong_ip_resolved"})

            if domain_ip != ip:
                raise serializers.ValidationError({"domain": "wrong_ip"})

        # Check SSH port connection
        if ssh_username and ssh_password and ssh_port:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)

            try:
                s.connect((ip, int(ssh_port)))
            except Exception:
                raise serializers.ValidationError({"ip": "ssh_port_connection_failed"})
            finally:
                s.shutdown(socket.SHUT_RDWR)
                s.close()

            # Check SSH credentials
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(ip, ssh_username, ssh_password, ssh_port)
                ssh.connect(ip, username=ssh_username, password=ssh_password, port=ssh_port, allow_agent=False, look_for_keys=False)
            except Exception:
                ssh.close()        
                raise serializers.ValidationError({"ip": "ssh_connection_failed"})

            _, stdout, _ = ssh.exec_command('cat /etc/system-release /etc/issue 2>/dev/null')
            ssh_output = stdout.read().lower().decode("utf-8") 
            ssh.close()        

            if ssh_output.find("centos") == -1 and ssh_output.find("ubuntu") == -1:
                raise serializers.ValidationError({"ip": "wrong_os"})
            
        return data

    class Meta:
        model = SelfHostedRadio
        exclude = ()

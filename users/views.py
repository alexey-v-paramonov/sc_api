from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response

from users.serializers import UserSerializer
from users.models import User


class Users(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_permissions(self):
        # Special case for signup
        if self.request.method == 'POST':
            self.permission_classes = (permissions.AllowAny,)

        return super(Users, self).get_permissions()

    def get(self, request, pk=None):

        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if user == request.user:
            serializer = UserSerializer(snippets, many=True)
            return Response(serializer.data)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk=None, format=None):

        # Create user
        if not pk:
            serializer = UserSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # not implemented yet
            return Response(status=status.HTTP_400_BAD_REQUEST)

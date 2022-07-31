from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
#from rest_framework_jwt.settings import api_settings
#from rest_framework_jwt.views import ObtainJSONWebToken
from users.serializers import UserSerializer
#, mJSONWebTokenSerializer
from users.models import User
from rest_framework import viewsets
from rest_framework import routers

class UsersView(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_permissions(self):
        # Special case for signup
        if self.request.method == 'POST':
            self.permission_classes = (permissions.AllowAny,)

        return super().get_permissions()

    # def get(self, request, pk=None):

    #     serializer = UserSerializer(request.user, many=False)
    #     return Response(serializer.data)

    # def post(self, request, pk=None, format=None):
    #     super().post(request, pk, format)
    #     # Create user
    #     if not pk:
    #         serializer = UserSerializer(data=request.data)

    #         if serializer.is_valid():
    #             user = serializer.save()

    #             jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    #             jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    #             payload = jwt_payload_handler(user)
    #             token = jwt_encode_handler(payload)

    #             return Response(
    #                 {"token": token},
    #                 status=status.HTTP_201_CREATED
    #             )

    #         return Response(
    #             serializer.errors, status=status.HTTP_400_BAD_REQUEST
    #         )

    #     else:
    #         # not implemented yet
    #         return Response(status=status.HTTP_400_BAD_REQUEST)


#class mObtainJSONWebToken(ObtainJSONWebToken):

#    serializer_class = mJSONWebTokenSerializer


#obtain_jwt_token = mObtainJSONWebToken.as_view()
users_router = routers.SimpleRouter()
users_router.register(r"users", UsersView)

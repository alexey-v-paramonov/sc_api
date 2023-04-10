from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from users.serializers import UserSerializer
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

class SCObtainAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"non_field_errors": "bad_credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    


users_router = routers.SimpleRouter()
users_router.register(r"users", UsersView)

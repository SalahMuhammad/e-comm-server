from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from auth.authentication import CustomAuthentication
from .models import User
from .serializers import UserSerializers
from auth.utilities import JWTUtilities
import datetime
from rest_framework.permissions import AllowAny


class RegisterView(APIView):
  serializer_class = UserSerializers

  def post(self, request):
    # i don't know why but line below throw unsupported media type, if content_type not application/json.
    # cuz it was in invalid format
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)
  

class LoginView(APIView):
  permission_classes = [AllowAny]

  def post(self, request):
    try:
      username = request.data['username']
      password = request.data['password']
    except KeyError:
      return Response(
        {'detail': 'Please provide your username and password.'}, 
        status=status.HTTP_400_BAD_REQUEST
      )
    
    user = User.objects.filter(username=username).first()
    if user is None:
      raise AuthenticationFailed({'username': 'User not found!'})

    if not user.check_password(password):
      raise AuthenticationFailed({'password': 'Incorrect password!'})#, code=status.HTTP_400_BAD_REQUEST)
    
    token = JWTUtilities.generate_jwt(user=user)

    response = Response()
    # response.set_cookie(key='jwt', value=token, expires=datetime.datetime.utcnow() + datetime.timedelta(days=7))
    response.data = {
      'jwt': token
    }
    response.status_code = status.HTTP_200_OK

    return response


class UserView(APIView):
  
  def get(self, request):
    # user = User.objects.filter(pk=payload['id']).first()
    serializer = UserSerializers(request.user)

    return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
  
  def post(self, request):
    response = Response()
    # response.delete_cookie('jwt')
    response.status_code = status.HTTP_204_NO_CONTENT

    return response

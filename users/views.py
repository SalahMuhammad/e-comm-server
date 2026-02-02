from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status, permissions
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
      # raise AuthenticationFailed({'username': 'User not found!'})
      raise AuthenticationFailed({'detail': 'Invalid credentials'})

    if not user.check_password(password):
      # raise AuthenticationFailed({'password': 'Incorrect password!'})
      raise AuthenticationFailed({'detail': 'Invalid credentials'})#, code=status.HTTP_400_BAD_REQUEST)
    
    if not user.is_active:
      raise AuthenticationFailed({'username': 'This account is inactive.'})
    
    token = JWTUtilities.generate_jwt(user=user)

    response = Response()
    # response.set_cookie(key='jwt', value=token, expires=datetime.datetime.utcnow() + datetime.timedelta(days=7))
    response.data = {
      'jwt': token,
      'username': username,
      'password_change_required': user.password_change_required
    }

    # response.set_cookie(
    #   key='jwt',
    #   value=token,
    #   httponly=True,
    #   expires=datetime.datetime.utcnow() + datetime.timedelta(days=7),
    #   # expires= datetime.datetime.utcnow() + datetime.timedelta(seconds=30),  # 7 days in seconds
    #   # samesite='Lax',
    #   samesite='strict', # Use 'strict' for better security, 'Lax' if you need cross-site requests
    #   # secure=False  # Set to True in production with HTTPS
    # )

    response.status_code = status.HTTP_200_OK

    return response


class UserView(APIView):
  permission_classes = [permissions.IsAuthenticated]
  
  def get(self, request):
    # user = User.objects.filter(pk=payload['id']).first()
    serializer = UserSerializers(request.user)

    return Response(serializer.data, status=status.HTTP_200_OK)

  def patch(self, request):
    user = request.user
    serializer = UserSerializers(user, data=request.data, partial=True)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
  
  def post(self, request):
    response = Response()
    # response.delete_cookie('jwt')
    response.status_code = status.HTTP_204_NO_CONTENT

    return response


class ChangePasswordView(APIView):
  """
  Allow users to change their password on first login.
  Requires current password, new password, and confirmation.
  """
  # Use IsAuthenticated instead of default DynamicPermission
  # so users with password_change_required can access this endpoint
  permission_classes = [permissions.IsAuthenticated]
  
  def post(self, request):
    user = request.user
    
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    # Validate input
    if not all([current_password, new_password, confirm_password]):
      return Response(
        {'detail': 'All fields are required.'},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    # Verify current password
    if not user.check_password(current_password):
      return Response(
        {'current_password': 'Current password is incorrect.'},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    # Check if new passwords match
    if new_password != confirm_password:
      return Response(
        {'confirm_password': 'Passwords do not match.'},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    # Set new password and remove password change requirement
    user.set_password(new_password)
    user.password_change_required = False
    user.save()
    
    return Response(
      {'detail': 'Password changed successfully.'},
      status=status.HTTP_200_OK
    )

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from auth.utilities import JWTUtilities
from django.contrib.sessions.models import Session
from users.models import User



class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # return (None, None)
        if request.build_absolute_uri().__contains__('8000/api/users/login/') or request.build_absolute_uri().__contains__('89/api/users/login/'):
            return (None, None)

        token = request.headers.get('auth', '')
        token = request.COOKIES.get('auth_0', '') + request.COOKIES.get('auth_1', '') if not token else token
        
        payload, verification_status = JWTUtilities.verify_jwt(token)

        if not verification_status:
            try:
                session = Session.objects.get(session_key=request.COOKIES.get('sessionid'))
                
                session_data = session.get_decoded()
                
                id = session_data.get('_auth_user_id')
                user = User.objects.get(pk=id)
                if user.is_superuser:
                    return (user, None)    
            except:
                raise AuthenticationFailed(f'Invalid token. {payload}')
            
            raise AuthenticationFailed(f'not superuser. {payload}')

        if request.method.lower() in ('post', 'put', 'patch'):
            # request.data['by'] = payload['id']
            mutable_data = request.data.copy()
            mutable_data['by'] = payload['id']
            request._full_data = mutable_data
        
        user = User.objects.get(pk=payload['id'])
        
        return (user, payload)


        # try:
        #     user = User.objects.get(pk=payload['id'])
        #     permissions = {
        #         'is_superuser': user.is_superuser,
        #         'is_staff': user.is_staff  # Note: it's "is_staff" not "is_stuff"
        #     }
        #     # if request.method != 'DELETE':
        #     request.data['by'] = user.id
        # except User.DoesNotExist:
        #     raise AuthenticationFailed('User not found.')
        #     # return None

        # return (user, permissions)

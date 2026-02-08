from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from auth.utilities import JWTUtilities
from django.contrib.sessions.models import Session
from users.models import User



class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # return (None, None)

        # Skip authentication for login endpoint
        if request.build_absolute_uri().__contains__('8000/api/users/login/') or request.build_absolute_uri().__contains__('89/api/users/login/'):
            return (None, None)
            
        # Allow restore endpoint to bypass auth if DB is broken (emergency hatch) or generally?
        # If we bypass auth, we must ensure permissions handle it or we relying on something else?
        # But RestoreDbBackup view requires IsSuperuser. IsSuperuser CHECKS user.
        # If I return (None, None), request.user is AnonymousUser.
        # IsSuperuser checks request.user.is_superuser. AnonymousUser.is_superuser is False.
        # So bypassing auth here will satisfy Authentication middleware, but fail Permission check.
        
        # If I want to allow restore when DB is broken, I need to open the permissions too.
        # But let's start by not crashing in `authenticate` when user table is missing.
        
        if request.build_absolute_uri().__contains__('/api/services/restore-db-backup/'):
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
            try:
                # Get existing data or use empty dict as fallback
                existing_data = request.data if request.data is not None else {}
                
                mutable_data = existing_data.copy() if hasattr(existing_data, 'copy') else dict(existing_data)
                mutable_data['by'] = payload['id']
                request._full_data = mutable_data
            except Exception as e:
                # If copying fails (e.g. file uploads in multipart requests),
                pass
            
        user = User.objects.get(pk=payload['id'])

        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        
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

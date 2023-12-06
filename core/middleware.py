from django.core.handlers.wsgi import WSGIRequest
import json
from core.models import User
from rest_framework import status
from django.utils import timezone
from django.http import JsonResponse

""" Middleware that is called on each request
"""
class LoginAttemptsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: WSGIRequest): 
        # get body of the request
        body = request.body

        # run view functions
        response = self.get_response(request)

        # verify path if is 'api/token'
        if request.path == "/api/token/":
            
            # get content of request
            content_type = request.headers.get("Content-Type", '').lower()

            # Getting email or None - in forms or jsons
            if 'application/json' in content_type:

                # if the content is a json:
                try:
                    email = json.loads(body.decode('utf-8')).get('email')
                except json.JSONDecodeError:
                    email = None

            elif 'application/x-www-form-urlencoded' in content_type:
                
                # if the content is a form:
                email = request.POST.get('email')
            
            else:
                email = None

            # if email recieved:
            if email:
                user = User.objects.get(email=email)

                # if user was created less than 3 minutes ago
                if timezone.now() <= (user.created_at + timezone.timedelta(minutes=3)):
                    return JsonResponse(
                    {'detail': 'Your account is in analysis. Try again later'},
                    status=status.HTTP_401_UNAUTHORIZED
                )    

                # if login is wrong:
                if user and response.status_code == status.HTTP_401_UNAUTHORIZED:
                    user.login_attempts += 1
                    user.save()

                    # if 3 wrong attempts, lock user for 15 minutes
                    if user.login_attempts ==3:
                        user.locked_at = timezone.now()
                        user.unlocked_at = timezone.now() + timezone.timedelta(minutes=15)
                        user.save()
                        
                        return JsonResponse(
                            {'detail': 'Blocked account. Try again in 15 minutes'},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                
                if user.login_attempts >= 3 and user.locked_at != None and user.unlocked_at != None and status.HTTP_200_OK:
                    if timezone.now() >= user.unlocked_at:
                        user.login_attempts = 0
                        user.locked_at = None
                        user.unlocked_at = None
                        user.save()
                    else:
                        return JsonResponse(
                            {'detail': 'Your account has been blocked. Try again later'},
                            status=status.HTTP_418_IM_A_TEAPOT
                        )
        
        return response

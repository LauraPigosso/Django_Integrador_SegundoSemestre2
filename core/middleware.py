from django.core.handlers.wsgi import WSGIRequest
import json
from core.models import User
from rest_framework import status
from django.utils import timezone
from django.http import JsonResponse

""" Middleware que é chamado a cada requisição
"""
class LoginAttemptsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: WSGIRequest): 
        # Obter corpo da requisição
        body = request.body

        # Executar funções de visualização
        response = self.get_response(request)

        # Verificar se o caminho é 'api/token'
        if request.path == "/api/token/":
            
            # Obter conteúdo da requisição
            content_type = request.headers.get("Content-Type", '').lower()

            # Obter email ou None - em formulários ou JSON
            if 'application/json' in content_type:

                # Se o conteúdo for um JSON:
                try:
                    email = json.loads(body.decode('utf-8')).get('email')
                except json.JSONDecodeError:
                    email = None

            elif 'application/x-www-form-urlencoded' in content_type:
                
                # Se o conteúdo for um formulário:
                email = request.POST.get('email')
            
            else:
                email = None

            # Se o email for recebido:
            if email:
                user = User.objects.get(email=email)

                # Se o usuário foi criado há menos de 3 minutos
                if timezone.now() <= (user.created_at + timezone.timedelta(minutes=3)):
                    return JsonResponse(
                    {'detail': 'Sua conta está em análise. Tente novamente mais tarde'},
                    status=status.HTTP_401_UNAUTHORIZED
                )    

                # Se o login estiver errado:
                if user and response.status_code == status.HTTP_401_UNAUTHORIZED:
                    user.login_attempts += 1
                    user.save()

                    # Se 3 tentativas erradas, bloquear o usuário por 15 minutos
                    if user.login_attempts == 3:
                        user.locked_at = timezone.now()
                        user.unlocked_at = timezone.now() + timezone.timedelta(minutes=15)
                        user.save()
                        
                        return JsonResponse(
                            {'detail': 'Conta bloqueada. Tente novamente em 15 minutos'},
                            status=status.HTTP_401_UNAUTHORIZED
                        )
                
                if user.login_attempts >= 3 and user.locked_at is not None and user.unlocked_at is not None and response.status_code == status.HTTP_200_OK:
                    if timezone.now() >= user.unlocked_at:
                        user.login_attempts = 0
                        user.locked_at = None
                        user.unlocked_at = None
                        user.save()
                    else:
                        return JsonResponse(
                            {'detail': 'Sua conta foi bloqueada. Tente novamente mais tarde'},
                            status=status.HTTP_418_IM_A_TEAPOT
                        )
        
        return response

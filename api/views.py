# Importações necessárias do Django REST framework e outros módulos
from rest_framework import viewsets, status, generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

# Importações específicas para autenticação JWT
from rest_framework_simplejwt import authentication as authenticationJWT

# Importações do Django para consultas no banco de dados
from django.db.models import Q

# Importações de modelos e serializadores da aplicação
from core import models
from api import serializers

# Importações adicionais para manipulação de datas e números
import random, decimal, datetime
from dateutil.relativedelta import relativedelta

# Definição de uma viewset para manipulação de contas
class AccountViewSet(viewsets.ModelViewSet):
    # Configurações básicas do viewset
    queryset = models.Account.objects.all()
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtra as contas apenas para o usuário autenticado e as ordena pela data de criação
        return self.queryset.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        # Escolhe o serializador com base na ação (retrieve, create, etc.)
        if self.action == 'retrieve' or self.action == 'create':
            return serializers.AccountDetailSerializer
        return serializers.AccountSerializer
    
    def create(self, request, *args, **kwargs):
        # Criação de uma nova conta
        serializer = serializers.AccountDetailSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                nickname = request.data['nickname']
            except:
                # Retorna um erro se o campo 'nickname' não estiver presente
                return Response({"error": "sem nickname"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Gera um número de conta aleatório
            account_number = "".join([str(random.randint(0, 9)) for _ in range(16)])

            # Cria uma nova conta com os dados fornecidos
            account = models.Account(
                user=self.request.user,
                number=account_number,
                agency="0001",
                nickname=nickname
            )

            account.balance = decimal.Decimal(0)
            account.save()

            return Response({'message': 'Conta Criada'}, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, url_path='withdraw')
    def withdraw(self, request, pk=None):
        # Realiza uma retirada de uma conta
        account = models.Account.objects.get(id=pk)
        serializer = serializers.ValueSerialzier(data=request.data)

        if serializer.is_valid():
            # Obtém o valor a ser retirado e o saldo atual da conta
            withdraw_value = decimal.Decimal(serializer.validated_data.get('value'))
            balance = decimal.Decimal(account.balance)

            comparar = balance.compare(withdraw_value)

            if comparar == 0 or comparar == 1:
                # Atualiza o saldo da conta e registra a transferência
                account.balance = 0 if balance - withdraw_value <= 0 else balance - withdraw_value
                account.save()
                self.save_in_tranfer(account.id, None, withdraw_value)

                return Response({"balance": account.balance}, status=status.HTTP_200_OK)
            
            # Retorna um erro se o saldo for insuficiente
            return Response({'message': 'saldo insuficiente'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Retorna erros de validação se o serializer não for válido
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=True, url_path='deposit')
    def deposit(self, request, pk=None):
        # Realiza um depósito em uma conta
        account = models.Account.objects.get(id=pk)
        serializer = serializers.ValueSerialzier(data=request.data)
        
        if serializer.is_valid():
            # Atualiza o saldo da conta e registra a transferência
            account.balance += decimal.Decimal(serializer.validated_data.get('value'))
            account.save()
            self.save_in_tranfer(None, account.id, serializer.validated_data.get('value'))

            return Response({'balance': account.balance}, status=status.HTTP_200_OK)

        # Retorna erros de validação se o serializer não for válido
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def save_in_tranfer(self, sender, receiver, value):
        # Salva informações de transferência usando um serializador específico
        transfer_serializer = serializers.CreateTransferDetailSerializer(
            data={
                "sender": sender,
                "receiver": receiver,
                "value": value,
                "description": ""
            }
        )
        transfer_serializer.is_valid(raise_exception=True)
        transfer_serializer.save()
    

# Definição de uma viewset para manipulação de transferências
class TansferViewSet(viewsets.GenericViewSet):
    queryset = models.Transfer.objects.all()

    def get_serializer_class(self):
        # Escolhe o serializador com base na ação (retrieve, create, etc.)
        if self.action == 'retrieve' or self.action == 'create':
            return serializers.TransferDetailSerializer
        return serializers.TransferSerializer

    def get_user(self):
        # Obtém o usuário da requisição
        return self.request.user
    
    def verify_account_balance(self, account_id, value):
        # Verifica se o saldo da conta é suficiente para a operação
        if value <= 0 or models.Account.objects.get(id=account_id).balance < value:
            return False
        return True

    def create(self, request):
        # Criação de uma nova transferência
        sender = request.data.get("sender")
        receiver = request.data.get("receiver")
        value = round(decimal.Decimal(request.data.get("value")), 2)
        description = request.data.get("description")

        if value < 0:
            # Retorna um erro se o valor da transferência for inválido
            return Response({'message': 'valor de transferencia invalido'}, status=status.HTTP_403_FORBIDDEN)
        elif models.Account.objects.get(id=sender).balance < value:
            # Retorna um erro se o saldo for insuficiente
            return Response({'message': 'No balance enough'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Verifica se a conta de envio pertence ao usuário autenticado
            if models.Account.objects.get(id=sender).user.id == request.user.id:
                # Cria a transferência e atualiza os saldos das contas
                transfer_serializer = serializers.TransferSerializer(
                    data={
                        "sender": sender,
                        "receiver": receiver,
                        "value": value,
                        "description": description
                    }
                )
                transfer_serializer.is_valid(raise_exception=True)
                transfer_serializer.save()

                accound_sender = models.Account.objects.get(id=sender)
                accound_sender.balance -= value
                accound_sender.save()

                accound_receiver = models.Account.objects.get(id=receiver)
                accound_receiver.balance += value
                accound_receiver.save()

                return Response({'message': 'Transferido'}, status=status.HTTP_200_OK)
            else:
                # Retorna um erro se a conta de envio não pertencer ao usuário autenticado
                return Response({'message': 'Esta conta não é do usuário logado'}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['GET'], detail=True, url_path='statement')
    def statement(self, request, pk=None):
        # Obtém o histórico de transferências de uma conta
        queryset = models.Transfer.objects.filter(
            Q(sender=pk) | Q(receiver=pk)
        ).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


# Definição de uma view para empréstimos
class LoanViewSet(generics.ListCreateAPIView):
    queryset = models.Loan.objects.all()
    serializer_class = serializers.LoanSerializer
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        # Criação de um novo empréstimo
        account = request.data.get("account")
        value = decimal.Decimal(request.data.get("value"))
        installments = int(request.data.get("installments"))

        min_value = 100
        min_installments = 1
        
        if value <= min_value:
            # Retorna um erro se o valor do empréstimo for muito baixo
            return Response({'message': f'o valor do empréstimo precisa ser pelo menos {min_value}'})
        elif installments <= min_installments:
            # Retorna um erro se o número de parcelas for muito baixo
            return Response({'message': f'o número de parcelas precisa ser de pelo menos {min_installments}'})
        else:
            # Registra o empréstimo e cria as parcelas correspondentes
            loan_serializer = serializers.LoanSerializer(
                data={
                    "value": value,
                    "installments": installments,
                    "account": account,
                }
            )
            loan_serializer.is_valid(raise_exception=True)
            loan_serializer.save()

            last_loan = models.Loan.objects.latest('id')

            for i in range(installments):
                # Calcula o valor e a data de vencimento de cada parcela
                installment_serializer = serializers.LoanInstallmentsSerializer(
                    data={
                        "value": round((value / installments * (last_loan.fees * i)), 2),
                        "due_date": datetime.datetime.combine(datetime.date.today() +  relativedelta(months=+i), datetime.datetime.min.time()),
                        "loanId": last_loan.pk,
                        "payed_date": None
                    }
                )
                installment_serializer.is_valid(raise_exception=True)
                installment_serializer.save()

            # Atualiza o saldo da conta do usuário
            user = models.Account.objects.get(id=account)
            user.balance += value
            user.save()

            return Response({'message': 'Loan Received'}, status=status.HTTP_201_CREATED)


# Definição de uma view para compras a prazo (créditos)
class CreditViewSet(generics.ListCreateAPIView):
    queryset = models.Credit.objects.all()
    serializer_class = serializers.CreditSerializer
    authentication_classes = [authenticationJWT.JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        # Criação de um novo crédito (compra a prazo)
        account = request.data.get("account")
        value = decimal.Decimal(request.data.get("value"))
        installments = int(request.data.get("installments"))

        max_value = 10000
        min_installments = 1

        if value > max_value:
            # Retorna um erro se o valor do crédito for muito alto
            return Response({'message': f'o valor precisa ser menor que {max_value}'})
        elif installments <= min_installments:
            # Retorna um erro se o número de parcelas for muito baixo
            return Response({'message': f'o número de parcelas precisa ser de pelo menos {min_installments}'})
        else:
            # Registra o crédito e cria as parcelas correspondentes
            credit_serializer = serializers.CreditSerializer(
                data={
                    "account": account,
                    "installments": installments,
                    "value": value
                }
            )
            credit_serializer.is_valid(raise_exception=True)
            credit_serializer.save()

            last_credit = models.Credit.objects.latest("id")

            for i in range(installments):
                # Calcula a data de vencimento de cada parcela
                due_date = datetime.datetime.now() + relativedelta(months=+i)
                due_date = datetime.datetime.combine(due_date, datetime.datetime.min.time())

                installments_serializer = serializers.CreditInstallmentsSerializer(
                    data={
                        "creditId": last_credit.pk,
                        "value": round((value / installments), 2),
                        "due_date": due_date.replace(day=5)
                    }
                )
                installments_serializer.is_valid(raise_exception=True)
                installments_serializer.save()
            return Response({'message': 'Credito criado'}, status=status.HTTP_201_CREATED)

    def list(self, request, pk=None):
        # Lista os créditos de um determinado usuário
        queryset = models.Credit.objects.filter(account=pk)
        serializer = serializers.CreditSerializer(queryset, many=True)

        return Response(serializer.data)
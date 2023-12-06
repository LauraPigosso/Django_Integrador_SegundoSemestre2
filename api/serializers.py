from rest_framework import serializers
from core.models import *
from user.serializers import UserSerializer

class AccountSerializer(serializers.ModelSerializer):
    # Serializa os dados do modelo Account
    class Meta:
        model = Account
        # Define os campos que serão incluídos na serialização
        fields = ['id', 'agency', 'number', 'nickname']
        # Define campos como somente leitura
        read_only_fields = ['number']

class AccountUserSerializer(serializers.ModelSerializer):
    # Estende AccountSerializer e inclui a serialização do usuário relacionado
    user = UserSerializer()
    
    class Meta:
        model = Account
        fields = ['id', 'agency', 'number', 'user', 'nickname']
        read_only_fields = ['number']

class AccountDetailSerializer(AccountSerializer):
    # Estende AccountSerializer e inclui campos adicionais
    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + ['id', 'balance', 'created_at', 'nickname']
        # Define campos adicionais como somente leitura
        read_only_fields = AccountSerializer.Meta.fields + ['id', 'balance', 'created_at']

class ValueSerialzier(serializers.Serializer):
    # Um serializador genérico para um único campo 'value' do tipo Decimal
    value = serializers.DecimalField(max_digits=8, decimal_places=2)

class TransferDetailSerializer(serializers.ModelSerializer):
    # Serializa os detalhes de uma transferência, incluindo informações do remetente e destinatário
    sender = AccountUserSerializer()
    receiver = AccountUserSerializer()
    value = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Transfer
        fields = ['value', 'sender', 'receiver', 'description']

class CreateTransferDetailSerializer(serializers.ModelSerializer):
    # Serializador para a criação de uma transferência, sem incluir informações completas dos usuários
    value = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Transfer
        fields = ['value', 'sender', 'receiver', 'description']

class TransferSerializer(serializers.ModelSerializer):
    # Serializador simplificado para a entidade Transfer
    sender = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), many=False)
    receiver = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), many=False)
    value = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Transfer
        fields = ['value', 'sender', 'receiver', 'description']

class LoanSerializer(serializers.ModelSerializer):
    # Serializa os dados do modelo Loan
    class Meta:
        model = Loan
        fields = ['account', 'installments', 'value']

class LoanInstallmentsSerializer(serializers.ModelSerializer):
    # Serializa os dados do modelo LoanInstallments com todos os campos
    class Meta:
        model = LoanInstallments
        fields = '__all__'

class CreditSerializer(serializers.ModelSerializer):
    # Serializa os dados do modelo Credit
    class Meta:
        model = Credit
        fields = ['account', 'installments', 'value']

class CreditInstallmentsSerializer(serializers.ModelSerializer):
    # Serializa os dados do modelo CreditInstallments com campos específicos
    class Meta:
        model = CreditInstallments
        fields = ['creditId', 'payed_date', 'due_date', 'value']

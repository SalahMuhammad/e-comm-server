from rest_framework import serializers
from .models import DebtSettlement
from common.encoder import MixedRadixEncoder


class DebtSettlementSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.name')
    by_username = serializers.ReadOnlyField(source='by.username')
    hashed_id = serializers.SerializerMethodField()


    class Meta:
        model = DebtSettlement
        fields = '__all__'
        extra_kwargs = {
            'by': {'write_only': True},
        }


    def get_hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)

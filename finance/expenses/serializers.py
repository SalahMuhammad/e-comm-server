from .models import Expense, Category
# 
from rest_framework import serializers
# 
from common.encoder import MixedRadixEncoder



class ExpensesSerializers(serializers.ModelSerializer):
	created_by = serializers.ReadOnlyField(source='created_by.username')
	last_updated_by = serializers.ReadOnlyField(source='last_updated_by.username')
	category_name = serializers.ReadOnlyField(source='category.name')
	payment_method_name = serializers.SerializerMethodField()
	hashed_id = serializers.SerializerMethodField()
	

	class Meta:
		model = Expense
		exclude = ['id']	
	
	def get_hashed_id(self, obj):
		return MixedRadixEncoder().encode(obj.id)
	
	def get_payment_method_name(self, obj):
		return f'{obj.business_account.account_type} - {obj.business_account.account_name}'



class CategorysSerializers(serializers.ModelSerializer):
	created_by = serializers.ReadOnlyField(source='created_by.username')
	last_updated_by = serializers.ReadOnlyField(source='last_updated_by.username')


	class Meta:
		model = Category
		fields = '__all__'

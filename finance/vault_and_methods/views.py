from django.http import Http404
from django.db.models.deletion import ProtectedError
from rest_framework import status
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from django.db import IntegrityError, transaction

from common.encoder import MixedRadixEncoder
# 
from .models import BusinessAccount, AccountType
from .services.account_balance_total import AccountBalance
from .services.filters import AccountsFilter
# 
from .serializers import BusinessAccountSerializer, AccountTypeSerializer
# django filters
from django_filters.rest_framework import DjangoFilterBackend




class ListCreateAccountsView(
	mixins.ListModelMixin,
	mixins.CreateModelMixin,
	GenericAPIView
):
	queryset = BusinessAccount.objects.select_related(
		'by',
		"account_type"
	).all()
	serializer_class = BusinessAccountSerializer
	# Adding filtering backends
	filter_backends = [DjangoFilterBackend]
	filterset_class = AccountsFilter

	
	def get(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)
	
	def perform_create(self, serializer):
		serializer.save(by=self.request.user)



class DetailAccountView(
	mixins.RetrieveModelMixin, 
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	GenericAPIView
):
	queryset = BusinessAccount.objects.select_related(
		'by',
		"account_type"
	).all()
	serializer_class = BusinessAccountSerializer


	def get_object(self):
		encoded_pk = self.kwargs.get('pk')
		try:
			decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
			return self.get_queryset().get(id=decoded_id)
		except Exception as e:
			print(f"Invalid encoded ID: {self.kwargs['pk']}")
			raise Http404("Object not found")

	def get(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	def patch(self, request,*args, **kwargs):
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		try:
			return super().destroy(request, *args, **kwargs)
		except ProtectedError:
			return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
	
	def perform_update(self, serializer):
		serializer.save(by=self.request.user)




# ------------------------ account type ----------------------------------------




class ListCreateAccountTypeView(
	mixins.ListModelMixin,
	mixins.CreateModelMixin,
	GenericAPIView
):
	queryset = AccountType.objects.select_related(
		'by',
	).all()
	serializer_class = AccountTypeSerializer


	def get(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)
	
	def perform_create(self, serializer):
		serializer.save(by=self.request.user)


class DetailAccountTypeView(
	mixins.RetrieveModelMixin, 
	mixins.UpdateModelMixin,
	mixins.DestroyModelMixin,
	GenericAPIView
):
	queryset = AccountType.objects.select_related(
		'by',
	).all()
	serializer_class = AccountTypeSerializer


	def get_object(self):
		encoded_pk = self.kwargs.get('pk')
		try:
			decoded_id = MixedRadixEncoder().decode(str(encoded_pk))
			return self.get_queryset().get(id=decoded_id)
		except Exception as e:
			print(f"Invalid encoded ID: {self.kwargs['pk']}")
			raise Http404("Object not found")

	def get(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	def patch(self, request,*args, **kwargs):
		return super().partial_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		try:
			return super().destroy(request, *args, **kwargs)
		except ProtectedError:
			return Response({'detail': 'لا يمكن حذف هذا العنصر قبل حذف المعاملات المرتبطه به اولا 😵...'}, status=status.HTTP_400_BAD_REQUEST)
	
	def perform_update(self, serializer):
		serializer.save(by=self.request.user)




# ------------------- analysis --------------------------------------




from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		return self.request.user.is_superuser


# class VaultBalanceAPIView(LoginRequiredMixin, APIView):
class VaultBalanceAPIView(APIView, SuperUserRequiredMixin):
	"""
	API endpoint to retrieve vault balance(s).
	
	Query parameters:
	- account_id: (optional) specific BusinessAccount pk
	- compute_all: (optional) 'true' to force computation from transactions
	
	Returns JSON with balance information.
	"""
	
	def get(self, request, *args, **kwargs):
		"""
		Retrieve account balance information for a business account or all accounts.
		This GET endpoint returns balance data with optional computation from all transactions.
		Query Parameters:
			account_id (str, optional): The ID of a specific business account. If provided,
				returns balance for that account only. If omitted, returns total balance
				across all active accounts and individual account details.
			compute_all (str, optional): Boolean flag ('true'/'false'). When 'true', forces
				balance computation by summing all transactions from scratch rather than
				using cached/current balance. Defaults to 'false'.
		Returns:
			Response: JSON response with the following structure:
				- Single account (account_id provided):
					{
						'success': bool,
						'account_id': int,
						'account_name': str,
						'balance': str,
						'computed_from_transactions': bool
					}
				- All accounts (account_id not provided):
					{
						'success': bool,
						'total_balance': str,
						'accounts': [
							{
								'id': int,
								'name': str,
								'balance': str  # or 'error' if computation failed
							}
						],
						'computed_from_transactions': bool
					}
		Raises:
			PermissionDenied (403): User lacks permission to view the requested account.
			BusinessAccount.DoesNotExist (404): Specified account_id does not exist.
			ValueError (400): Invalid parameter values.
			Exception (500): Unexpected server error.
		Note:
			'computed_from_transactions': Indicates whether the balance was calculated by
			summing all individual transactions (True) or retrieved from a cached/current
			balance field (False). When True, the balance reflects the most accurate state
			by recalculating from transaction history. When False, it uses a pre-calculated
			stored value for performance.
		"""
		try:
			account_id = request.GET.get('account_id')
			compute_all = request.GET.get('compute_all', '').lower() == 'true'
			
			# Get balance
			if account_id:
				account = get_object_or_404(BusinessAccount, pk=account_id)
				
				# Check permissions (customize based on your permission system)
				if not self.has_permission(request.user, account):
					raise PermissionDenied("You don't have permission to view this account")

				acc_instance = AccountBalance(account_id, compute_all)
				balance = acc_instance.get_account_or_accounts_balance()

				return Response({
					'success': True,
					'account_id': account.id,
					'account_name': str(account.account_name),
					'balance': str(balance),
					'computed_from_transactions': compute_all or account.current_balance is None
				})
			else:
				acc_instance = AccountBalance(is_computed_from_transactions=compute_all)
				balance = acc_instance.get_account_or_accounts_balance()
				
				# Get individual account balances
				accounts = BusinessAccount.objects.filter(is_active=True)
				account_details = []
				
				for acc in accounts:
					if self.has_permission(request.user, acc):
						try:
							acc_instance.acc = acc
							acc_balance = acc_instance.get_account_or_accounts_balance()

							account_details.append({
								'id': acc.id,
								'name': str(acc.account_name),
								'balance': str(acc_balance)
							})
						except Exception as e:
							account_details.append({
								'id': acc.id,
								'name': str(acc.account_name),
								'error': str(e)
							})
				
				return Response({
					'success': True,
					'total_balance': str(balance),
					'accounts': account_details,
					'computed_from_transactions': compute_all
				})
				
		except BusinessAccount.DoesNotExist:
			return Response({
				'success': False,
				'error': 'Account not found'
			}, status=404)
			
		except ValueError as e:
			return Response({
				'success': False,
				'error': str(e)
			}, status=400)
			
		except PermissionDenied as e:
			return Response({
				'success': False,
				'error': str(e)
			}, status=403)
			
		except Exception as e:
			return Response({
				'success': False,
				'error': f'An error occurred: {str(e)}'
			}, status=500)
	
	def has_permission(self, user, account):
		"""
		Check if user has permission to view account balance.
		Customize this based on your permission system.
		"""
		# Example: Check if user is staff or superuser
		if user.is_staff or user.is_superuser:
			return True
		
		# Example: Check if account has user permission field
		if hasattr(account, 'allowed_users'):
			return user in account.allowed_users.all()
		
		# Default: allow all authenticated users (customize as needed)
		return True


class VaultBalanceDashboardView(LoginRequiredMixin, TemplateView):
	"""
	Template view to display vault balances in a dashboard.
	"""
	template_name = 'finance/vault_balance_dashboard.html'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		try:
			# Get total balance
			total_balance = get_total_money_in_vaults(account=None)
			context['total_balance'] = total_balance
			
			# Get individual account balances
			accounts = BusinessAccount.objects.filter(is_active=True)
			account_balances = []
			
			for acc in accounts:
				if self.has_permission(self.request.user, acc):
					try:
						balance = get_total_money_in_vaults(account=acc)
						account_balances.append({
							'account': acc,
							'balance': balance,
							'error': None
						})
					except Exception as e:
						account_balances.append({
							'account': acc,
							'balance': None,
							'error': str(e)
						})
			
			context['account_balances'] = account_balances
			context['has_error'] = any(ab['error'] for ab in account_balances)
			
		except Exception as e:
			context['error'] = str(e)
			context['total_balance'] = None
			context['account_balances'] = []
		
		return context
	
	def has_permission(self, user, account):
		"""Check if user has permission to view account balance."""
		if user.is_staff or user.is_superuser:
			return True
		if hasattr(account, 'allowed_users'):
			return user in account.allowed_users.all()
		return True


class RecalculateVaultBalanceView(LoginRequiredMixin, APIView):
	"""
	View to recalculate vault balance from transactions.
	Useful for admin/maintenance operations.
	"""
	
	def post(self, request, *args, **kwargs):
		# Check if user has permission (staff/superuser only)
		if not request.user.is_staff and not request.user.is_superuser:
			raise PermissionDenied("Only staff members can recalculate balances")
		
		try:
			account_id = request.POST.get('account_id')
			
			if account_id:
				account = get_object_or_404(BusinessAccount, pk=account_id)
				
				# Compute balance from transactions
				computed_balance = get_total_money_in_vaults(
					account=account,
					is_explicit_compute_all_transactions=True
				)
				
				# Update current_balance if field exists
				if hasattr(account, 'current_balance'):
					old_balance = account.current_balance
					account.current_balance = computed_balance
					account.save(update_fields=['current_balance'])
					
					return Response({
						'success': True,
						'account_id': account.id,
						'account_name': str(account),
						'old_balance': str(old_balance) if old_balance else None,
						'new_balance': str(computed_balance),
						'updated': True
					})
				else:
					return Response({
						'success': True,
						'account_id': account.id,
						'account_name': str(account),
						'computed_balance': str(computed_balance),
						'updated': False,
						'message': 'Account does not have current_balance field'
					})
			else:
				# Recalculate all accounts
				accounts = BusinessAccount.objects.filter(is_active=True)
				results = []
				
				for acc in accounts:
					try:
						computed_balance = get_total_money_in_vaults(
							account=acc,
							is_explicit_compute_all_transactions=True
						)
						
						if hasattr(acc, 'current_balance'):
							old_balance = acc.current_balance
							acc.current_balance = computed_balance
							acc.save(update_fields=['current_balance'])
							
							results.append({
								'account_id': acc.id,
								'account_name': str(acc),
								'old_balance': str(old_balance) if old_balance else None,
								'new_balance': str(computed_balance),
								'updated': True
							})
						else:
							results.append({
								'account_id': acc.id,
								'account_name': str(acc),
								'computed_balance': str(computed_balance),
								'updated': False
							})
					except Exception as e:
						results.append({
							'account_id': acc.id,
							'account_name': str(acc),
							'error': str(e)
						})
				
				return Response({
					'success': True,
					'accounts_processed': len(results),
					'results': results
				})
				
		except Exception as e:
			return Response({
				'success': False,
				'error': str(e)
			}, status=500)





















from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from datetime import date, datetime
# from decimal import Decimal
from typing import List, Optional
from .services.AccountMovementService import AccountMovementService
from .serializers import (
	AccountMovementResponseSerializer,
	BalanceHistoryItemSerializer,
	# MovementFiltersSerializer,
	# MovementSerializer,
	# MovementSummarySerializer,
	AccountSummarySerializer
)



class AccountMovementListView(APIView, SuperUserRequiredMixin):
	"""
	Get account movements with optional filtering.
	
	Query Parameters:
		- start_date (YYYY-MM-DD): Start date filter
		- end_date (YYYY-MM-DD): End date filter
		- account_id (int): Single account ID filter
		- account_ids (comma-separated ints): Multiple account IDs filter
		- include_pending (bool): Include pending transactions (default: false)
	
	Examples:
		GET /api/account-movements/
		GET /api/account-movements/?account_id=5
		GET /api/account-movements/?start_date=2025-01-01&end_date=2025-01-31
		GET /api/account-movements/?account_id=5&start_date=2025-01-01
		GET /api/account-movements/?account_ids=5,7,9&include_pending=true
	"""
	# permission_classes = [IsAuthenticated]
	
	def get(self, request):
		try:
			# Parse query parameters
			start_date = self._parse_date(request.query_params.get('start_date'))
			end_date = self._parse_date(request.query_params.get('end_date'))
			account_id = self._parse_int(request.query_params.get('account_id'))
			account_ids = self._parse_int_list(request.query_params.get('account_ids'))
			include_pending = request.query_params.get('include_pending', 'false').lower() == 'true'
			
			# Validate that account_id and account_ids are not both provided
			if account_id and account_ids:
				return Response(
					{'detail': 'Cannot specify both account_id and account_ids'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Get movements from service
			result = AccountMovementService.get_movements(
				start_date=start_date,
				end_date=end_date,
				account_id=account_id,
				account_ids=account_ids,
				include_pending=include_pending
			)

			# Serialize response
			serializer = AccountMovementResponseSerializer(result)

			return Response(serializer.data, status=status.HTTP_200_OK)
			
		except ValueError as e:
			return Response(
				{'error': f'Invalid parameter: {str(e)}'},
				status=status.HTTP_400_BAD_REQUEST
			)
		except Exception as e:
			return Response(
				{'error': f'An error occurred: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
	@staticmethod
	def _parse_date(date_string: Optional[str]) -> Optional[date]:
		"""Parse date string to date object"""
		if not date_string:
			return None
		parsed = parse_date(date_string)
		if not parsed:
			raise ValueError(f'Invalid date format: {date_string}. Use YYYY-MM-DD')
		return parsed
	
	@staticmethod
	def _parse_int(value: Optional[str]) -> Optional[int]:
		"""Parse integer parameter"""
		if not value:
			return None
		try:
			return int(value)
		except ValueError:
			raise ValueError(f'Invalid integer: {value}')
	
	@staticmethod
	def _parse_int_list(value: Optional[str]) -> Optional[List[int]]:
		"""Parse comma-separated integer list"""
		if not value:
			return None
		try:
			return [int(x.strip()) for x in value.split(',') if x.strip()]
		except ValueError:
			raise ValueError(f'Invalid integer list: {value}')


class AccountBalanceHistoryView(APIView):
	"""
	Get balance history for a specific account.
	
	URL Parameters:
		- account_id (int): Required account ID
	
	Query Parameters:
		- start_date (YYYY-MM-DD): Start date filter
		- end_date (YYYY-MM-DD): End date filter
	
	Examples:
		GET /api/account-movements/5/balance-history/
		GET /api/account-movements/5/balance-history/?start_date=2025-01-01&end_date=2025-01-31
	"""
	permission_classes = [IsAuthenticated]
	
	def get(self, request, account_id):
		try:
			# Parse query parameters
			start_date = self._parse_date(request.query_params.get('start_date'))
			end_date = self._parse_date(request.query_params.get('end_date'))
			
			# Get balance history from service
			history = AccountMovementService.get_account_balance_history(
				account_id=account_id,
				start_date=start_date,
				end_date=end_date
			)
			
			# Serialize response
			serializer = BalanceHistoryItemSerializer(history, many=True)
			
			return Response({
				'account_id': account_id,
				'start_date': start_date,
				'end_date': end_date,
				'history': serializer.data,
				'count': len(history)
			}, status=status.HTTP_200_OK)
			
		except ValueError as e:
			return Response(
				{'error': f'Invalid parameter: {str(e)}'},
				status=status.HTTP_400_BAD_REQUEST
			)
		except Exception as e:
			return Response(
				{'error': f'An error occurred: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
	@staticmethod
	def _parse_date(date_string: Optional[str]) -> Optional[date]:
		"""Parse date string to date object"""
		if not date_string:
			return None
		parsed = parse_date(date_string)
		if not parsed:
			raise ValueError(f'Invalid date format: {date_string}. Use YYYY-MM-DD')
		return parsed


class MultiAccountSummaryView(APIView):
	"""
	Get summary statistics for multiple accounts.
	
	Query Parameters:
		- account_ids (comma-separated ints): Required account IDs
		- start_date (YYYY-MM-DD): Start date filter
		- end_date (YYYY-MM-DD): End date filter
	
	Examples:
		GET /api/account-movements/multi-summary/?account_ids=5,7,9
		GET /api/account-movements/multi-summary/?account_ids=5,7,9&start_date=2025-01-01
	"""
	permission_classes = [IsAuthenticated]
	
	def get(self, request):
		try:
			# Parse query parameters
			account_ids_str = request.query_params.get('account_ids')
			if not account_ids_str:
				return Response(
					{'error': 'account_ids parameter is required'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			account_ids = self._parse_int_list(account_ids_str)
			start_date = self._parse_date(request.query_params.get('start_date'))
			end_date = self._parse_date(request.query_params.get('end_date'))
			
			# Get multi-account summary from service
			summary = AccountMovementService.get_multi_account_summary(
				account_ids=account_ids,
				start_date=start_date,
				end_date=end_date
			)
			
			# Serialize response
			serialized_summary = {
				str(account_id): AccountSummarySerializer(data).data
				for account_id, data in summary.items()
			}
			
			return Response({
				'start_date': start_date,
				'end_date': end_date,
				'accounts': serialized_summary,
				'total_accounts': len(summary)
			}, status=status.HTTP_200_OK)
			
		except ValueError as e:
			return Response(
				{'error': f'Invalid parameter: {str(e)}'},
				status=status.HTTP_400_BAD_REQUEST
			)
		except Exception as e:
			return Response(
				{'error': f'An error occurred: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
	@staticmethod
	def _parse_date(date_string: Optional[str]) -> Optional[date]:
		"""Parse date string to date object"""
		if not date_string:
			return None
		parsed = parse_date(date_string)
		if not parsed:
			raise ValueError(f'Invalid date format: {date_string}. Use YYYY-MM-DD')
		return parsed
	
	@staticmethod
	def _parse_int_list(value: str) -> List[int]:
		"""Parse comma-separated integer list"""
		try:
			result = [int(x.strip()) for x in value.split(',') if x.strip()]
			if not result:
				raise ValueError('Empty account list')
			return result
		except ValueError:
			raise ValueError(f'Invalid integer list: {value}')


class AccountMovementExportView(APIView):
	"""
	Export account movements to CSV format.
	
	Query Parameters: Same as AccountMovementListView
	
	Examples:
		GET /api/account-movements/export/?account_id=5&start_date=2025-01-01
	"""
	permission_classes = [IsAuthenticated]
	
	def get(self, request):
		import csv
		from django.http import HttpResponse
		
		try:
			# Parse query parameters (same as AccountMovementListView)
			start_date = self._parse_date(request.query_params.get('start_date'))
			end_date = self._parse_date(request.query_params.get('end_date'))
			account_id = self._parse_int(request.query_params.get('account_id'))
			account_ids = self._parse_int_list(request.query_params.get('account_ids'))
			include_pending = request.query_params.get('include_pending', 'false').lower() == 'true'
			
			# Get movements from service
			result = AccountMovementService.get_movements(
				start_date=start_date,
				end_date=end_date,
				account_id=account_id,
				account_ids=account_ids,
				include_pending=include_pending
			)
			
			# Create CSV response
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = f'attachment; filename="account_movements_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
			
			writer = csv.writer(response)
			
			# Write headers
			writer.writerow([
				'Date', 'Type', 'Reference', 'Account', 'Party', 
				'Related Document', 'Amount In', 'Amount Out', 'Status', 'Notes'
			])
			
			# Write data
			for movement in result['movements']:
				writer.writerow([
					movement['date'].strftime('%Y-%m-%d %H:%M:%S'),
					movement['type_display'],
					movement['reference'],
					movement['account_name'],
					movement['party'],
					movement['related_doc'] or '',
					movement['amount_in'],
					movement['amount_out'],
					movement['status'],
					movement['notes']
				])
			
			# Write summary
			writer.writerow([])
			writer.writerow(['Summary'])
			writer.writerow(['Total In', result['summary']['total_in']])
			writer.writerow(['Total Out', result['summary']['total_out']])
			writer.writerow(['Net Movement', result['summary']['net_movement']])
			writer.writerow(['Total Transactions', result['summary']['count']])
			
			return response
			
		except ValueError as e:
			return Response(
				{'error': f'Invalid parameter: {str(e)}'},
				status=status.HTTP_400_BAD_REQUEST
			)
		except Exception as e:
			return Response(
				{'error': f'An error occurred: {str(e)}'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
	@staticmethod
	def _parse_date(date_string: Optional[str]) -> Optional[date]:
		if not date_string:
			return None
		parsed = parse_date(date_string)
		if not parsed:
			raise ValueError(f'Invalid date format: {date_string}. Use YYYY-MM-DD')
		return parsed
	
	@staticmethod
	def _parse_int(value: Optional[str]) -> Optional[int]:
		if not value:
			return None
		try:
			return int(value)
		except ValueError:
			raise ValueError(f'Invalid integer: {value}')
	
	@staticmethod
	def _parse_int_list(value: Optional[str]) -> Optional[List[int]]:
		if not value:
			return None
		try:
			return [int(x.strip()) for x in value.split(',') if x.strip()]
		except ValueError:
			raise ValueError(f'Invalid integer list: {value}')

import json
from django.http import JsonResponse



class JSONOnlyMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		content_type = request.content_type
		method = request.method


		if request.build_absolute_uri().__contains__('/logout/'):
			return self.get_response(request)
		
		if request.build_absolute_uri().__contains__('/api/items/'):
			return self.get_response(request)
		
		if request.build_absolute_uri().__contains__('8000/admin') or request.build_absolute_uri().__contains__('89/admin'):
			return self.get_response(request)

		if request.build_absolute_uri().__contains__('/login/'):
			return self.get_response(request)
		
		if method in ('OPTIONS', 'DELETE'):
			return self.get_response(request)
		
		if request.build_absolute_uri().__contains__('8000/api/refillable-sys/'):
			return self.get_response(request)
		
		if request.build_absolute_uri().__contains__('8000/api/payment/'):
			return self.get_response(request)
		
		if request.build_absolute_uri().__contains__('8000/api/sales/return/'):
			return self.get_response(request)
		
		if not content_type == 'application/json' and method not in ['GET']:
			return JsonResponse(
				{
				'detail': 'Unsupported media type. Please send data in JSON format.'
				}, 
				status=415,
				content_type='application/json'
			)

		return self.get_response(request)

import json
import os
from datetime import datetime
from pathlib import Path
# ليةعلاقة بمعرفة ما اذا كان الطلب من كلاس ولا فنكشن
# class RequestLogMiddleware(MiddlewareMixin):
class RequestLogMiddleware():
	# def __init__(self, get_response):
	# 	self.get_response = get_response

	# def __call__(self, request):
	# 	if request.build_absolute_uri().__contains__('/api/users/login/'):
	# 		return self.get_response(request)
		
	# 	if request.build_absolute_uri().__contains__('/login/'):
	# 		return self.get_response(request)
		
	# 	if request.build_absolute_uri().__contains__('/admin/'):
	# 		return self.get_response(request)

	# 	url = request.build_absolute_uri()
	# 	method = request.method
	# 	# body = request.body.decode('utf-8') if request.body else None
	# 	headers = {key: value for key, value in request.headers.items() if key.lower() != 'authorization'}

	# 	res = self.get_response(request)

	# 	if request.method in ['POST', 'PATCH', 'PUT', 'DELETE']:
	# 		if headers['Origin'].__contains__('localhost:8000'):
	# 			try:
	# 				session = Session.objects.get(session_key=request.COOKIES.get('sessionid'))
					
	# 				session_data = session.get_decoded()
					
	# 				id = session_data.get('_auth_user_id')
	# 			except (Session.DoesNotExist, User.DoesNotExist):
	# 				return JsonResponse(
	# 					{
	# 						'detail': 'Session expired. Please login again.'
	# 					},
	# 					status=401,
	# 					content_type='application/json'
	# 				)
	# 		else:
	# 			paylod, s = JWTUtilities.verify_jwt(headers['Auth'])
	# 			id = paylod['id'] if paylod else None
			
	# 		RequestLog.objects.create(
	# 			by_id=id,
	# 			method=method,
	# 			url=url,
	# 			headers=headers,
	# 			# body=json.loads(body) if request.content_type == 'application/json' else json.dumps(dict(request.POST)),
	# 			response_status=res.status_code,
	# 			# response_body=json.loads(res.content.decode('utf-8')) if request.content_type == 'application/json' else res.data,
	# 		)

	# 	return res	

	def __init__(self, get_response):
		self.get_response = get_response
		# Create base directory for request logs
		self.base_log_dir = Path('request_logs')
		self.base_log_dir.mkdir(exist_ok=True)
		# Create directories for each method
		for method in ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']:
			(self.base_log_dir / method.lower()).mkdir(exist_ok=True)

	def save_request_log(self, user, method, url, headers, body, response_status, response_body):
		username = user.username if user else ''
		timestamp = datetime.now().strftime(f"{username}_%Y-%m-%d_%H:%M:%S_%f")
		method_dir = self.base_log_dir / method.lower()
		filename = f"{timestamp}.json"
        
		log_data = {
			'timestamp': timestamp,
			'url': url,
			'headers': headers,
			'request_body': body,
			'response_status': response_status,
			'response_body': response_body
		}
        
		with open(method_dir / filename, 'w', encoding='utf-8') as f:
			json.dump(log_data, f, indent=4, ensure_ascii=False)

	def __call__(self, request):
        # Capture request data
		url = request.build_absolute_uri()

		if url.lower().__contains__('png'):
			return self.get_response(request)
		
		if url.lower().__contains__('jpeg'):
			return self.get_response(request)
		
		if url.lower().__contains__('jpg'):
			return self.get_response(request)
		
		if url.lower().__contains__('gif'):
			return self.get_response(request)
		

		method = request.method
		headers = 'none'
		if hasattr(request, 'headers'):
			headers = {k: v for k, v in request.headers.items() 
				if k.lower() != 'auth'}
        
        # Capture request body
		if request.content_type == 'application/json':
			try:
				body = json.loads(request.body) if request.body else None
			except json.JSONDecodeError:
				body = dict(request.POST)
			except:
				body = 'an exception occurred while decoding the body.'
		else:
			body = None
        # Get response
		response = self.get_response(request)

        # Capture response data
		response_body = 'none'
		try:
			response_body = json.loads(response.content.decode('utf-8'))
		except json.JSONDecodeError:
			response_body = response.content.decode('utf-8')
		except Exception as e:
			pass

        # Save to file
		if method in ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']:

			# Save to file and database
			self.save_request_log(
				user=request.user,
				method=method,
				url=url,
				headers=headers,
				body=body,
				response_status=response.status_code if hasattr(response, 'status_code') else None,
				response_body=response_body
			)

			# # Create database log
			# RequestLog.objects.create(
			# 	by_id=user_id,
			# 	method=method,
			# 	url=url,
			# 	headers=headers,
			# 	response_status=response.status_code
			# )

		return response

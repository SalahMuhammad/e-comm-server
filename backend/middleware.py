import json
from django.http import JsonResponse
from datetime import datetime
from pathlib import Path
from django.forms.models import model_to_dict
from django.urls import resolve



class JSONOnlyMiddleware:
    """
    Middleware to enforce JSON content-type for mutation requests 
    while excluding specific authentication, admin, and utility endpoints.
    """
    EXCLUDED_PATHS = (
        '/logout/',
        '/login/',
        '/admin/',
        '/api/items/',
        '/api/finance/debt-settlement/',
        '/api/refillable-sys/',
        '/api/payment/',
        '/api/sales/return/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        method = request.method

        # Skip checks for safe/exempt methods and excluded paths
        if method in ('OPTIONS', 'DELETE'):
            return self.get_response(request)

        if any(excluded in path for excluded in self.EXCLUDED_PATHS):
            return self.get_response(request)

        # Enforce application/json for data-mutating requests
        if request.content_type != 'application/json' and method not in ('GET',):
            return JsonResponse(
                {
                    'detail': 'Unsupported media type. Please send data in JSON format.'
                }, 
                status=415,
                content_type='application/json'
            )

        return self.get_response(request)



class RequestLogMiddleware:
    """
    Advanced logging middleware that records request/response lifecycles
    and tracks exact field-by-field modifications (old vs new values) for mutations.
    """
    IGNORED_EXTENSIONS = ('.png', '.jpeg', '.jpg', '.gif', '.ico', '.css', '.js')

    def __init__(self, get_response):
        self.get_response = get_response
        self.base_log_dir = Path('request_logs')
        self.base_log_dir.mkdir(exist_ok=True)
        
        for method in ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']:
            (self.base_log_dir / method.lower()).mkdir(exist_ok=True)

    def _extract_body(self, request):
        """Safely extracts request body as JSON or fallback dictionary."""
        if request.content_type == 'application/json':
            try:
                return json.loads(request.body.decode('utf-8')) if request.body else None
            except (json.JSONDecodeError, UnicodeDecodeError):
                return 'An exception occurred while decoding the body.'
        return dict(request.POST) if request.POST else None

    def _get_object_state_before_mutation(self, request):
        """
        Dynamically resolves the Django view, extracts the model and primary key (pk/id)
        from the URL, and captures the old database state before changes are applied.
        """
        if request.method not in ['PUT', 'PATCH', 'DELETE']:
            return None

        try:
            resolved = resolve(request.path)
            view_class = getattr(resolved.func, 'cls', None)
            
            if view_class:
                # Extract model from class-based view queryset or model attribute
                model = getattr(view_class, 'queryset', None)
                if model is not None and hasattr(model, 'model'):
                    model = model.model
                elif hasattr(view_class, 'model'):
                    model = view_class.model
                else:
                    model = None

                if model:
                    pk = resolved.kwargs.get('pk') or resolved.kwargs.get('id')
                    if pk:
                        instance = model.objects.filter(pk=pk).first()
                        if instance:
                            return model_to_dict(instance)
        except Exception:
            pass
        return None

    def _generate_mutation_comparison(self, method, old_state, request_body):
        """
        Computes a precise field-by-field diff containing ONLY the fields that changed.
        """
        if method == 'DELETE':
            return {
                'action_type': 'DELETION',
                'deleted_object_state': old_state if old_state else 'Record not found or already deleted'
            }

        if method in ['PUT', 'PATCH'] and isinstance(request_body, dict):
            field_changes = {}

            if old_state:
                for field, new_val in request_body.items():
                    old_val = old_state.get(field, 'N/A')
                    # Record only if the value actually changed
                    if str(old_val) != str(new_val):
                        field_changes[field] = {
                            'old_value': old_val,
                            'new_value': new_val
                        }
            else:
                # Fallback if the instance couldn't be resolved dynamically
                for field, new_val in request_body.items():
                    field_changes[field] = {
                        'old_value': 'Unknown (Instance not resolved)',
                        'new_value': new_val
                    }

            return {
                'action_type': 'MODIFICATION',
                'changed_fields_only': field_changes,
                'total_fields_modified': len(field_changes)
            }

        return None

    def save_request_log(self, user, method, url, headers, body, old_state, response_status, response_body):
        username = user.username if (user and user.is_authenticated) else 'anonymous'
        timestamp = datetime.now().strftime(f"{username}_%Y-%m-%d_%H:%M:%S_%f")
        method_dir = self.base_log_dir / method.lower()
        filename = f"{timestamp}.json"
        
        # Generate clean field-by-field diff comparison
        mutation_comparison = self._generate_mutation_comparison(method, old_state, body)

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'url': url,
            'headers': headers,
            'request_body': body,
            'mutation_comparison': mutation_comparison,
            'response_status': response_status,
            'response_body': response_body
        }
        
        try:
            with open(method_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def __call__(self, request):
        path = request.path

        if path.lower().endswith(self.IGNORED_EXTENSIONS):
            return self.get_response(request)

        method = request.method
        url = request.build_absolute_uri()
        
        headers = 'none'
        if hasattr(request, 'headers'):
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ('auth', 'authorization')}

        body = self._extract_body(request)

        # Capture old state BEFORE view/mutation execution
        old_state = self._get_object_state_before_mutation(request)

        # Proceed with request handling
        response = self.get_response(request)

        response_body = 'none'
        try:
            response_body = json.loads(response.content.decode('utf-8'))
        except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
            response_body = response.content.decode('utf-8', errors='ignore') if hasattr(response, 'content') else 'No content'

        if method in ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']:
            self.save_request_log(
                user=getattr(request, 'user', None),
                method=method,
                url=url,
                headers=headers,
                body=body,
                old_state=old_state,
                response_status=getattr(response, 'status_code', None),
                response_body=response_body
            )

        return response

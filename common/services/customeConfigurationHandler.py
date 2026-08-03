from services.models import AppConfiguration


def get_config_data():
    """Helper to safely retrieve the config JSON data from the singleton model."""
    config_record = AppConfiguration.objects.filter(pk=1).first()
    return config_record.data if config_record else {}


def customeFilters(obj, queryset, key):
    customeConfig = get_config_data().get(key, {})

    if obj.request.user.is_superuser:
        return queryset

    users = customeConfig.get("defaultFilters", {}).get("users", [])
    filters = customeConfig.get("defaultFilters", {}).get("filters", {})

    if obj.request.user.username in users:
        return queryset.filter(**filters)

    return queryset


def customeViewsUserPermissionHandler(user, ___view_id):
    if not ___view_id:
        return False

    if user.is_superuser:
        return True

    customeConfig = get_config_data().get("customeViewsUserPermission", {})
    allowed_users = customeConfig.get(___view_id, [])

    if user.username in allowed_users:
        return True

    return False

def hideFieldsConfigBased(self, field_list):
    request = self.context.get('request')
    if not request: return

    if request.user.is_superuser: return

    # 1. Get the actual underlying HTTP method to catch OPTIONS requests
    if hasattr(request, '_request'):
        method = str(request._request.method).lower() # Safely captures 'options'
    else:
        method = str(request.method).lower()

    key = self.Meta.model.__name__.lower()
    config = AppConfiguration.objects.all()[0]
    
    try:
        method_config = config.data['serializers']['hideFields'][key][method]
    except KeyError:
        return

    if request.user and request.user.username in method_config['users']:
        for field in method_config['fields']:
            field_list.pop(field, None)

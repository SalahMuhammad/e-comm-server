from django.urls import NoReverseMatch
from rest_framework.reverse import reverse as drf_reverse


def get_relation_info(model, field_name):
    """
    Analyzes a model field to determine its relationship type and related model.
    """
    try:
        model_field = model._meta.get_field(field_name)

        if not (model_field.many_to_one or model_field.one_to_many or 
                model_field.many_to_many or model_field.one_to_one):
            return None
        
        # Determine relationship type
        relation_type = None
        if model_field.many_to_one: # Standard ForeignKey
            relation_type = 'many_to_one'
        elif model_field.one_to_many: # Reverse ForeignKey
            relation_type = 'one_to_many'
        elif model_field.many_to_many:
            relation_type = 'many_to_many'
        elif model_field.one_to_one:
            relation_type = 'one_to_one'

        return {
            'is_relation': relation_type is not None,
            'type': relation_type,
            'related_model': model_field.related_model,
            'is_reverse': getattr(model_field, 'one_to_many', False)
        }
    except Exception:
        return None

def resolve_model_endpoint(model, request):
    """
    Attempts to find the standard DRF List URL for a given model.
    """
    if not model:
        return None
        
    model_name = model._meta.model_name
    # Try common naming patterns
    patterns = [f"{model_name}-list", f"api:{model_name}-list"]
    
    for pattern in patterns:
        try:
            return drf_reverse(pattern, request=request)
        except NoReverseMatch:
            continue
    return None

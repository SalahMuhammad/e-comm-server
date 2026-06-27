from django.urls import NoReverseMatch
from rest_framework.reverse import reverse as drf_reverse


def get_relation_info(model, field_name):
    try:
        model_field = model._meta.get_field(field_name)

        if not (model_field.many_to_one or model_field.one_to_many or 
                model_field.many_to_many or model_field.one_to_one):
            return None
        
        relation_type = None
        if model_field.many_to_one:
            relation_type = 'many_to_one'
        elif model_field.one_to_many:
            relation_type = 'one_to_many'
        elif model_field.many_to_many:
            relation_type = 'many_to_many'
        elif model_field.one_to_one:
            relation_type = 'one_to_one'

        is_reverse = getattr(model_field, 'one_to_many', False)
        related_model = model_field.related_model

        result = {
            'is_relation': relation_type is not None,
            'type': relation_type,
            # 'related_model': related_model,
            'is_reverse': is_reverse,
        }

        # For reverse FK: get FKs declared on the related model (e.g. TransactionSpareParts)
        # For forward FK: get FKs declared on the current model itself
        target_model = related_model if is_reverse else model

        seen = set()
        related_models = []
        for fk in get_model_foreign_keys(target_model):
            if fk.related_model not in seen:
                seen.add(fk.related_model)
                related_models.append(fk.related_model)

        result.update({
            'related_models': related_models,
        })

        return result
    except Exception:
        return None

# def resolve_model_endpoint(model, request, modelList = []):
def resolve_model_endpoint(request, modelList = []):
    """
    Attempts to find the standard DRF List URL for a given model.
    """
    if not modelList:
        return None
    
    if modelList:
        endpoints = {}
        for m in modelList:
            model_name = m._meta.model_name        
            patterns = [f"{model_name}-list", f"api:{model_name}-list"]

            for pattern in patterns:
                try:
                    # return drf_reverse(pattern, request=request)
                    endpoints[model_name] = drf_reverse(pattern, request=request)
                except NoReverseMatch:
                    continue

        return endpoints
    return None

def get_model_foreign_keys(model):
    """
    Returns all forward ForeignKey fields on a model.
    """
    return [
        field for field in model._meta.get_fields()
        if field.many_to_one and not field.one_to_many  # forward FK only, no reverse accessors
    ]

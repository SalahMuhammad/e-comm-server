from rest_framework.metadata import SimpleMetadata
from utils.api_inspectors import get_relation_info, resolve_model_endpoint
from django.forms import Textarea


class RelationshipMetadataMixin(SimpleMetadata):
    def determine_metadata(self, request, view):
        # 1. Get standard DRF metadata (labels, choices, etc.)
        metadata = super().determine_metadata(request, view)
        
        # 2. Safety check for serializer/model
        serializer = getattr(view, 'get_serializer', lambda: None)()
        model = getattr(serializer.Meta, 'model', None) if serializer else None
        
        if not model or 'actions' not in metadata:
            return metadata

        # 3. Inject our custom logic
        for action in metadata['actions'].values():
            for field_name, field_info in action.items():
                rel_info = get_relation_info(model, field_name)
                
                if rel_info:
                    field_info['is_foreign_key'] = True
                    field_info['relation_type'] = rel_info['type']
                    field_info['is_reverse'] = rel_info['is_reverse']

                    field_info['endpoints'] = resolve_model_endpoint(
                        modelList=rel_info['related_models'], 
                        request=None
                    )
                    
        return metadata



class FieldTypeMetadataMixin(SimpleMetadata):
    """
    Metadata class to distinguish between single-line text inputs 
    and multi-line textarea fields.
    """
    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)
        
        serializer = getattr(view, 'get_serializer', lambda: None)()
        if not serializer or 'actions' not in metadata:
            return metadata

        for action in metadata['actions'].values():
            for field_name, field_info in action.items():
                serializer_field = serializer.fields.get(field_name)
                
                if serializer_field:
                    style = serializer_field.style
                    template = style.get('base_template') or style.get('template')
                    
                    # Detect if DRF or Django forms treated this as a textarea
                    is_textarea_widget = isinstance(getattr(serializer_field, 'widget', None), Textarea)
                    
                    if template == 'textarea.html' or is_textarea_widget:
                        field_info['ui_type'] = 'textarea'
                    else:
                        field_info['ui_type'] = 'text_input'
                        
        return metadata


class CompositeMetadata(FieldTypeMetadataMixin, RelationshipMetadataMixin):
    pass


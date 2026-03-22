from rest_framework.metadata import SimpleMetadata
from utils.api_inspectors import get_relation_info, resolve_model_endpoint


class RelationshipMetadata(SimpleMetadata):
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
                    field_info['foreign_model'] = rel_info['related_model'].__name__
                    
                    # Resolve URL
                    field_info['endpoint'] = resolve_model_endpoint(
                        rel_info['related_model'], 
                        request=None
                    )
                    
        return metadata

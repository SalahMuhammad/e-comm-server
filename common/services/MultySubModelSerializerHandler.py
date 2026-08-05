import json
from django.db import transaction
from rest_framework import serializers
from django.db.utils import IntegrityError

class WritableMultipleNestedSubmodelsMixin:
    """
    Mixin to handle multiple writable nested submodels.
    Configure `SUBMODEL_CONFIGS` like:
    {
        'parts': {'model': TransactionSpareParts, 'fk': 'maintenance'},
        'attachments': {'model': Attachment, 'fk': 'maintenance'},
    }
    """
    SUBMODEL_CONFIGS = {}

    def to_internal_value(self, data):
        # Determine if request.FILES is available (DRF passes it inside self.context['request'])
        request = self.context.get('request')
        files = request.FILES if request else None

        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        validated_raw = {}

        for field_name in self.SUBMODEL_CONFIGS.keys():
            json_field_name = f"{field_name}_json"
            raw_rows = None

            if field_name in mutable and isinstance(mutable[field_name], (list, tuple)):
                raw_rows = mutable.pop(field_name)
            elif json_field_name in mutable:
                pj = mutable.get(json_field_name, '')
                if pj:
                    try:
                        raw_rows = json.loads(pj)
                    except json.JSONDecodeError as exc:
                        raise serializers.ValidationError({json_field_name: f'Invalid JSON: {exc}'})
                mutable.pop(json_field_name, None)

            if raw_rows is not None:
                # Inject files from request.FILES if they follow a naming convention like: {field_name}_file_{index}
                if files:
                    for idx, row in enumerate(raw_rows):
                        file_key = f"{field_name}_file_{idx}"

                        if file_key in files:
                            row['_file_obj'] = files[file_key]

                validated_raw[field_name] = raw_rows

        validated = super(WritableMultipleNestedSubmodelsMixin, self).to_internal_value(mutable)
        validated['_raw_multi_submodel_rows'] = validated_raw
        return validated

    def validate(self, attrs):
        attrs = super().validate(attrs)
        raw_data_map = attrs.pop('_raw_multi_submodel_rows', {})
        all_field_errors = {}
        clean_data_map = {}

        for field_name, raw_rows in raw_data_map.items():
            row_errors = []
            clean_rows = []
            has_errors = False

            for row in raw_rows:
                action = row.get('_action', 'existing')
                err = {}

                if action == 'existing':
                    clean_rows.append({'_action': 'existing', '_row': row})
                    row_errors.append({})
                    continue

                if action in ('create', 'update'):
                    try:
                        validator_method = getattr(self, f'validate_{field_name}_row', self.validate_submodel_row)
                        row = validator_method(row, action)
                    except serializers.ValidationError as e:
                        err.update(e.detail if isinstance(e.detail, dict) else {'non_field_errors': e.detail})

                elif action == 'delete':
                    row_id = row.get('id')
                    if not row_id:
                        clean_rows.append({'_action': 'skip'})
                        row_errors.append({})
                        continue
                    clean_rows.append({'_action': 'delete', 'id': row_id})
                    row_errors.append({})
                    continue

                if err:
                    has_errors = True
                clean_rows.append({**row, '_action': action})
                row_errors.append(err)

            if has_errors:
                all_field_errors[field_name] = row_errors
            clean_data_map[field_name] = clean_rows

        if all_field_errors:
            raise serializers.ValidationError(all_field_errors)

        attrs['_clean_multi_submodel_rows'] = clean_data_map
        return attrs

    def validate_submodel_row(self, row, action):
        return row

    @transaction.atomic
    def create(self, validated_data):
        multi_rows = validated_data.pop('_clean_multi_submodel_rows', {})
        instance = super().create(validated_data)
        self._apply_multi_submodel_rows(instance, multi_rows)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        multi_rows = validated_data.pop('_clean_multi_submodel_rows', {})

        prepare_method = getattr(self, f'prepare_update_data', self.prepare_update_data)
        validated_data = prepare_method(instance, validated_data)

        instance = super().update(instance, validated_data)
        self._apply_multi_submodel_rows(instance, multi_rows)
        return instance

    def prepare_update_data(self, instance, validated_data):
        return validated_data

    def _apply_multi_submodel_rows(self, instance, multi_rows):
        for field_name, rows in multi_rows.items():
            config = self.SUBMODEL_CONFIGS.get(field_name)
            if not config:
                continue
            submodel_cls = config['model']
            fk_name = config['fk']

            for row in rows:
                action = row.get('_action')
                if action in ('existing', 'skip'):
                    continue
                elif action == 'create':
                    create_hook = getattr(self, f'get_{field_name}_create_kwargs', self.get_submodel_create_kwargs)
                    kwargs = create_hook(instance, row)
                    kwargs[fk_name] = instance
                    try:
                        submodel_cls.objects.create(**kwargs)
                    except IntegrityError as e:
                        raise serializers.ValidationError(
                            {'detail': str(e)}
                        )
                elif action == 'update':
                    row_id = row.get('id')
                    if not row_id:
                        create_hook = getattr(self, f'get_{field_name}_create_kwargs', self.get_submodel_create_kwargs)
                        kwargs = create_hook(instance, row)
                        kwargs[fk_name] = instance
                        submodel_cls.objects.create(**kwargs)
                        continue
                    try:
                        sub_obj = submodel_cls.objects.get(pk=row_id, **{fk_name: instance})
                    except submodel_cls.DoesNotExist:
                        raise serializers.ValidationError(
                            {field_name: f'Record with id {row_id} does not belong to this parent instance.'}
                        )
                    update_hook = getattr(self, f'get_{field_name}_update_kwargs', self.get_submodel_update_kwargs)
                    update_kwargs = update_hook(instance, row, sub_obj)
                    for key, val in update_kwargs.items():
                        setattr(sub_obj, key, val)
                    try:
                        sub_obj.save()
                    except IntegrityError as e:
                        raise serializers.ValidationError(
                            {'detail': str(e)}
                        )
                elif action == 'delete':
                    row_id = row.get('id')
                    submodel_cls.objects.filter(pk=row_id, **{fk_name: instance}).delete()

    def get_submodel_create_kwargs(self, instance, row):
        return row

    def get_submodel_update_kwargs(self, instance, row, sub_obj):
        return row

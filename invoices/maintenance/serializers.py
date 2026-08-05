from rest_framework import serializers

from common.encoder import MixedRadixEncoder
from common.services.MultySubModelSerializerHandler import WritableMultipleNestedSubmodelsMixin
from common.services.NumberValidator import NumberValidator
from common.services.customeConfigurationHandler import append_value_if_user_has_no_permission_to_field, hideFieldsConfigBased
from common.utility.audit_info_dateformatter import audit_info_dateformatter
from items.services.validate_items_stock import ValidateItemsStock

from .models import Maintenance, TransactionSpareParts
from items.models import Items
from datetime import date


class SparePartLineSerializer(serializers.ModelSerializer):
    """
    Serializer for a single TransactionSpareParts row.

    Incoming shape (from the client's parts array):
        {
            "id":         <int|null>,   # null for new rows
            "spare_part": <int>,        # FK to Items
            "quantity":   "1.50",
            "_action":    "create" | "update" | "delete" | "existing"
        }

    _action is not a model field — we pop it in the parent serializer
    before calling save/delete.
    """

    # Write with a PK, read back with the object so the client gets the name.
    # spare_part_id = serializers.PrimaryKeyRelatedField(
    #     queryset=Items.objects.all(),
    #     source='spare_part',
    #     write_only=False,
    # )
    _spare_part_name = serializers.ReadOnlyField(source='spare_part.name')
    _repository_name = serializers.ReadOnlyField(source='repository.name')
    _audit_info = serializers.SerializerMethodField()


    class Meta:
        model = TransactionSpareParts
        fields = ['id', '_spare_part_name', 'spare_part', 'quantity', 'repository', '_repository_name', '_audit_info']
        read_only_fields = ['id', '_spare_part_name', '_audit_info']

    def get__audit_info(self, obj):
        return audit_info_dateformatter(obj)

    # def get__spare_part(self, obj):
    #     return {'id': obj.spare_part_id, 'name': obj.spare_part.name}


class MaintenanceSerializer(WritableMultipleNestedSubmodelsMixin, serializers.ModelSerializer):
    """
    Full Maintenance serializer with writable nested spare parts.

    The `parts` key is NOT a regular nested serializer field — it arrives as
    a JSON string in `parts_json` (from the Next.js FormData) OR as a plain
    list when the client sends application/json.  We normalise both in
    to_internal_value() and store the parsed list on the instance so
    create() / update() can handle it.

    The `_action` field on each part row is consumed here and never reaches
    the SparePartLineSerializer.
    """

    """
    Full Maintenance serializer with reusable writable nested submodels support.
    """
    SUBMODEL_CONFIGS = {
        'parts': {'model': TransactionSpareParts, 'fk': 'maintenance'},
    }


    _client_name = serializers.ReadOnlyField(source='client.name')
    _item_name = serializers.ReadOnlyField(source='item.name')
    _maintained_by_name = serializers.SerializerMethodField()
    # parts = TransactionSparePartsSerializer(many=True, read_only=False, required=False)
    _hashed_id = serializers.SerializerMethodField()
    _audit_info = serializers.SerializerMethodField()



    # Read-only nested representation returned in GET responses
    parts = SparePartLineSerializer(many=True, required=False)

    # Accept `parts_json` as a write-only JSON string (FormData path)
    parts_json = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # client  = serializers.PrimaryKeyRelatedField(queryset=Party.objects.all())
    # item    = serializers.PrimaryKeyRelatedField(queryset=Items.objects.all())
    # by      = serializers.PrimaryKeyRelatedField(
    #     queryset=Employee.objects.all(), allow_null=True, required=False
    # )

    class Meta:
        model = Maintenance
        fields = [
            # 'id',
            'client',
            'serial_number',
            'item',
            'status',           # read-only in practice (set by model.save())
            'date_in',
            'maintenance_date',
            'date_out',
            'maintained_by',
            'malfunctions',
            'notes',
            'parts',            # read
            'parts_json',       # write (FormData path)
            '_client_name', '_item_name', '_maintained_by_name', '_hashed_id', '_audit_info',
            'cost'
        ]
        read_only_fields = ['id', 'status', '_maintained_by_name']
        extra_kwargs = {
            # 'date_in': {'required': False},
            # 'malfunctions': {'allow_null': True},
            # 'notes': {'allow_null': True},
            # 'age': {'required': False, 'allow_null': True}
        }


    def get_fields(self):
        feilds = super().get_fields()

        hideFieldsConfigBased(self, feilds)
        return feilds
    
    def get__hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)
    
    def get__audit_info(self, obj):
        return audit_info_dateformatter(obj)
    
    def get__maintained_by_name(self, obj):
        return f"{obj.maintained_by.first_name} {obj.maintained_by.last_name}" if obj.maintained_by else " - "

    def validate_parts_row(self, row, action):
        """Custom row logic scoped specifically to the 'parts' field."""
        err = {}
        sp_id = row.get('spare_part')
        if not sp_id:
            err['spare_part'] = 'This field is required.'
        else:
            try:
                row['_spare_part_obj'] = Items.objects.get(pk=sp_id)
            except Items.DoesNotExist:
                err['spare_part'] = f'Item with id {sp_id} does not exist.'

        v, error = NumberValidator._coerce_to_numeric(row.get('quantity', 1))
        if error:
            err['quantity'] = error    
        elif v <= 0 or v >= 9999999.99:
            err['quantity'] = 'unsupported value'
        else:
            row['_qty_decimal'] = v

        # a = ValidateItemsStock()
        # items_ids = [item.item.id for item in invoice.s_invoice_items.all()]
        # a.validate_stock(items=Items.objects.filter(id__in=items_ids), create_error_file=False)
        

        if err:
            raise serializers.ValidationError(err)
        return row

    def validate(self, data):
        attrs = super(MaintenanceSerializer, self).validate(data)

        # Fallback to existing instance values if doing a partial update (PATCH)
        date_in = data.get('date_in', getattr(attrs, 'date_in', date.today()))
        maintenance_date = data.get('maintenance_date', getattr(attrs, 'maintenance_date', None))
        date_out = data.get('date_out', getattr(attrs, 'date_out', None))
        print(attrs, 222222222)
        errors = {}

        # 1. Maintenance date cannot be before date_in
        if maintenance_date and date_in and maintenance_date < date_in:
            errors['maintenance_date'] = "Maintenance date cannot be earlier than the entry date (date_in)."

        # 2. Date out cannot be before date_in
        if date_out and date_in and date_out < date_in:
            errors['date_out'] = "Exit date (date_out) cannot be earlier than the entry date (date_in)."

        # 3. Date out should not be before maintenance date (if both are provided)
        if date_out and maintenance_date and date_out < maintenance_date:
            errors['date_out'] = "Exit date (date_out) cannot be earlier than the maintenance date."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def prepare_update_data(self, instance, validated_data):
        return append_value_if_user_has_no_permission_to_field(
            'maintenance', 
            self.context.get('request'),
            instance,
            validated_data
        )

    def get_parts_create_kwargs(self, instance, row):
        return {
            'spare_part': row['_spare_part_obj'],
            'quantity': row['_qty_decimal'],
            'repository_id': row['repository'] or 10000,
            'created_by': instance.created_by,
            'last_updated_by': instance.last_updated_by
        }

    def get_parts_update_kwargs(self, instance, row, sub_obj):
        return {
            'spare_part': row['_spare_part_obj'],
            'quantity': row['_qty_decimal'],
            'repository_id': row['repository'] or 10000,
            'last_updated_by': instance.last_updated_by,
        }

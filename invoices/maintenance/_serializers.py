from rest_framework import serializers
from .models import Maintenance, TransactionSpareParts
from common.encoder import MixedRadixEncoder



class TransactionSparePartsSerializer(serializers.ModelSerializer):
    spare_part_name = serializers.ReadOnlyField(source='spare_part.name')

    class Meta:
        model = TransactionSpareParts
        fields = ['id', 'spare_part', 'spare_part_name', 'quantity', 'created_at', 'last_updated_at']


class MaintenanceSerializer(serializers.ModelSerializer):
    _client_name = serializers.ReadOnlyField(source='client.name')
    _item_name = serializers.ReadOnlyField(source='item.name')
    _by_username = serializers.ReadOnlyField(source='by.username')
    parts = TransactionSparePartsSerializer(many=True, read_only=False, required=False)
    _hashed_id = serializers.SerializerMethodField()
    _audit_info = serializers.SerializerMethodField()


    def get__hashed_id(self, obj):
        return MixedRadixEncoder().encode(obj.id)

    def get__audit_info(self, obj):
        diff = obj.last_updated_at - obj.created_at
        total_seconds = int(diff.total_seconds())

        # Break into components
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        # Build the string based on conditions
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        time_diff = f"{' '.join(parts)}"

        return {
            'created_at': obj.created_at.strftime('%Y.%m.%d %H:%M:%S'),
            'created_by': obj.created_by.username,
            'last_updated_at': obj.last_updated_at.strftime('%Y.%m.%d %H:%M:%S'),
            'last_updated_by': obj.last_updated_by.username,
            'time_diff': time_diff
        }

    class Meta:
        model = Maintenance
        fields = [
            'id', 'client', '_client_name', 'serial_number', 'item', '_item_name',
            'status', 'date_in', 'maintenance_date', 'date_out', 'by', '_by_username',
            'malfunctions', 'notes', 'parts',
            '_hashed_id', '_audit_info'
        ]
        read_only_fields = ['status', '_audit_info', 'created_by', 'last_updated_by', 'created_at', 'last_updated_at']

    def create(self, validated_data):
        parts_data = validated_data.pop('parts', [])
        maintenance = Maintenance.objects.create(**validated_data)
        for part_data in parts_data:
            TransactionSpareParts.objects.create(maintenance=maintenance, **part_data)
        return maintenance

    def update(self, instance, validated_data):
        parts_data = validated_data.pop('parts', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if parts_data is not None:
            instance.parts.all().delete()
            for part_data in parts_data:
                TransactionSpareParts.objects.create(maintenance=instance, **part_data)

        return instance

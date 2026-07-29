from rest_framework import serializers



class ItemsFiltersSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.CharField(allow_blank=True))
    filters = serializers.JSONField()


class MaintenanceOptionalFieldsSerializer(serializers.Serializer):
    # Changed to CharField to support string values ("")
    maintainable_items = serializers.CharField(allow_blank=True)
    spare_parts = serializers.CharField(allow_blank=True)


class MaintenanceOptionalFiltersSerializer(serializers.Serializer):
    fields = MaintenanceOptionalFieldsSerializer()


class ItemsSectionSerializer(serializers.Serializer):
    defaultFilters = ItemsFiltersSerializer()
    maintenance_optional_filters = MaintenanceOptionalFiltersSerializer()


class MaintenanceDefaultFiltersSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.CharField(allow_blank=True))
    filters = serializers.JSONField()


class MaintenanceSectionSerializer(serializers.Serializer):
    defaultFilters = MaintenanceDefaultFiltersSerializer()


class CustomViewsUserPermissionSerializer(serializers.Serializer):
    buyerSupplier_view = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    buyerSupplier_creditBalanceList = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    buyerSupplier_accountStatement = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    vaultMthod_balance = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    vaultMthod_accountMovements = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    reportsWarehouse_itemMovement = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    items_itemFluctuation = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    sales_totalItemsSoldIn = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    sales_analysisCashDeferredPercentages = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    refillableItems_refundableItemsClientHas = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    refillableItems_itemUnitCost = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )
    # Made optional and allowed to be empty to prevent deletion/failure on missing inputs
    services_configuration = serializers.ListField(
        child=serializers.CharField(allow_blank=True)
    )


class ConfigurationMainSerializer(serializers.Serializer):
    items = ItemsSectionSerializer()
    maintenance = MaintenanceSectionSerializer()
    customeViewsUserPermission = CustomViewsUserPermissionSerializer()

    def update(self, instance, validated_data):
        instance.data = validated_data
        instance.save()
        return instance

    def to_representation(self, instance):
        return instance.data

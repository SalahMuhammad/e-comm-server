from django.db import models
from django.db.models import Q
from django.conf import settings
from datetime import datetime
from rest_framework.exceptions import ValidationError
from year_closure.models import ClosurePeriod
from django.db.models import Sum



class MyQuerySet(models.QuerySet):
    def optimized(
        self, 
        select_fields=None, 
        prefetch_fields=None, 
        use_select=True, 
        use_prefetch=True
    ):
        """
        Dynamically applies select_related and prefetch_related optimization.
        
        :param select_fields: Iterable of strings for select_related. 
                              Defaults to ['item', 'repository', 'created_by', 'updated_by'] if None.
        :param prefetch_fields: Iterable of strings or Prefetch objects for prefetch_related.
        :param use_select: Boolean flag to enable or skip select_related entirely.
        :param use_prefetch: Boolean flag to enable or skip prefetch_related entirely.
        """
        qs = self
        
        if use_select:
            fields_to_select = select_fields if select_fields is not None else []
            if fields_to_select:
                qs = qs.select_related(*fields_to_select)
                
        if use_prefetch:
            fields_to_prefetch = prefetch_fields if prefetch_fields is not None else []
            if fields_to_prefetch:
                qs = qs.prefetch_related(*fields_to_prefetch)
                
        return qs

    def for_repository(self, repository):
        """Filters queryset by repository instance, ID, or name."""
        if not repository:
            return self
        if isinstance(repository, (int, str)):
            return self.filter(repository_id=repository)
        return self.filter(repository=repository)

    def date_range(self, start_date=None, end_date=None, field_name='date'):
        """
        Filters queryset within an inclusive date range using any specified date field.
        Supported field names: 'date', 'issue_date', 'invoice__issue_date', etc.
        """
        qs = self
        if start_date:
            qs = qs.filter(**{f"{field_name}__gte": start_date})
        if end_date:
            qs = qs.filter(**{f"{field_name}__lte": end_date})
        return qs

    def accumulate(self, field_name):
        """Calculates the total accumulated quantity for the filtered queryset."""
        result = self.aggregate(total=Sum(field_name))
        return result['total'] or 0

    def accumulate_by(self, field_name, by_fields_as_tuple):
        """Groups the accumulated quantities by item."""
        return self.values(
            # 'item_id', 
            # 'item__name'  # Adjust to match your Items model field name
            by_fields_as_tuple
        ).annotate(
            total_quantity=Sum(field_name)
        ).order_by('item__name')



class _ActiveManager(models.Manager):
    def get_queryset(self):
        # queryset = super().get_queryset()
        queryset = MyQuerySet(self.model, using=self._db)

        YCS = settings.YEAR_COLSEURE_SETTINGS

        is_active_only  = YCS["is_active_only"]
        specific_period = YCS["specific"]
        
        input_date_format   = "%Y-%m-%d"
        is_periodical_fetch = not is_active_only == 1 and specific_period['from_date'] and specific_period['to_date']

        if is_periodical_fetch:
            from_date   = datetime.strptime(specific_period['from_date'], input_date_format)
            to_date     = datetime.strptime(specific_period['to_date'], input_date_format)

            if from_date > to_date:
                raise ValueError("from_date must be greater than to_date...")
        
        first_item = queryset.first()
        if first_item:
            field_name = _key_name_lookup(first_item)

        if is_periodical_fetch and first_item:
            return queryset.filter(
                Q(**{
                    f"{field_name}__gte":from_date,
                    f"{field_name}__lte":to_date,
                })
            )

        if is_active_only:
            locked_periods = ClosurePeriod.objects.filter(is_locked=True)

            # Build a single combined Q object for all locked date ranges
            locked_q = Q()
            for period in locked_periods:
                locked_q |= Q(**{
                    f"{field_name}__gte": period.from_date,
                    f"{field_name}__lte": period.to_date
                })
            
            if locked_periods.exists() and locked_q:
                return queryset.exclude(locked_q)
            
        return queryset



class _AllManager(models.Manager):
    def get_queryset(self):
        return MyQuerySet(self.model, using=self._db)

    def optimized(self, select_fields=None, prefetch_fields=None, use_select=True, use_prefetch=True):
        return self.get_queryset().optimized(
            select_fields=select_fields, 
            prefetch_fields=prefetch_fields, 
            use_select=use_select, 
            use_prefetch=use_prefetch
        )



def _check_if_period_is_locked(model, action='create'):
    """
    Checks if a record's date falls within a locked closure period.
    action: 'create', 'update', or 'delete'
    """
    if False:
        order_date = getattr(model, 'created_at', None)

    order_date = getattr(model, _key_name_lookup(model), None)

    if not order_date:
        return

    is_locked = ClosurePeriod.objects.filter(
        is_locked=True,
        from_date__lte=order_date,
        to_date__gte=order_date
    ).exists()

    if is_locked:
        if action == 'create':
            raise ValidationError({"detail": "Cannot add new records to a locked financial period."})
        elif action == 'update':
            raise ValidationError({"detail": "This record belongs to a locked financial period and cannot be modified."})
        elif action == 'delete':
            raise ValidationError({"detail": "This record belongs to a locked financial period and cannot be deleted."})


def _key_name_lookup(instance):
    if getattr(instance, "date", None):
        return "date"
    elif getattr(instance, "issue_date", None):
        return "issue_date"
    elif getattr(instance, "invoice", None):
        return "invoice__issue_date"
    else:
        raise ValueError("unknown key name _key_name_lookup(): line 121")



class YearClosureUtilClass(models.Model):
    objects = _AllManager()
    active_objects = _ActiveManager()


    def clean(self):
        super().clean()
        action = 'update' if self.pk else 'create'
        _check_if_period_is_locked(self, action=action)

    def delete(self, *args, **kwargs):
        _check_if_period_is_locked(self, action="delete")
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()            
        super().save(*args, **kwargs)



    class Meta:
        abstract = True

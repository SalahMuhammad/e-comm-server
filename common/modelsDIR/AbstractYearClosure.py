from django.db import models
from django.db.models import Q
from django.conf import settings
from datetime import datetime
from rest_framework.exceptions import ValidationError
from year_closure.models import ClosurePeriod



class _ActiveManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()

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

        if is_periodical_fetch:
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
    objects = models.Manager()
    active_objects = _ActiveManager()


    def clean(self):
        super().clean()
        action = 'update' if self.pk else 'create'
        _check_if_period_is_locked(self, action=action)

    def delete(self, *args, **kwargs):
        _check_if_period_is_locked(self, action="delete")
        super().delete(*args, **kwargs)



    class Meta:
        abstract = True

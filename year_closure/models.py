from django.db import models
from common.modelsDIR.AbstractAuditClasses import UpdatedCreatedByV2
from rest_framework.exceptions import ValidationError



class ClosurePeriod(UpdatedCreatedByV2):
    from_date = models.DateField()
    to_date = models.DateField()
    is_locked = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.from_date and self.to_date:
            # 1. Ensure logical date sequence
            if self.from_date > self.to_date:
                raise ValidationError("The 'from_date' cannot be later than the 'to_date'.")
            
            # 2. Disable intersection / overlap of periods
            overlapping = ClosurePeriod.objects.filter(
                from_date__lte=self.to_date,
                to_date__gte=self.from_date
            )
            
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
                
            if overlapping.exists():
                raise ValidationError("This closure period intersects with an existing closure period.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "LOCKED" if self.is_locked else "OPEN"
        return f"Closure: {self.from_date} to {self.to_date} ({status})"

from django.db import models
from common.modelsDIR.AbstractAuditClasses import UpdatedCreatedBy


class Repositories(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    

    def __str__(self):
        return self.name


    class Meta:
        ordering = ['id']

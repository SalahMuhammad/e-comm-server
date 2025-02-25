from django.db import models
from users.models import User
# from django.utils.timezone import now

class UpdatedCreatedBy(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    by = models.ForeignKey(User, on_delete=models.PROTECT)

    # @property
    # def alive(self):
    #     return (now() - updated_at).days < 7

    class Meta:
        abstract = True


class AbstractInvoicesOwners(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)


    class Meta:
        abstract = True
        ordering = ['name']


    def __str__(self) -> str:
        return self.name
    
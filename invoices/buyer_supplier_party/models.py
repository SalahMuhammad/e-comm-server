# models
from django.db import models
from django.db.models import OuterRef, Subquery, Sum, DecimalField, Value, Q, Count
from django.db.models.functions import Coalesce
from common.modelsDIR.AbstractAuditClasses import UpdatedCreatedBy
from common.modelsDIR.AbstractYearClosure import YearClosureUtilClass
# uatils
from django.utils.timezone import now
from django.conf import settings
from collections import defaultdict
from decimal import Decimal



class Party(UpdatedCreatedBy):
    name = models.CharField(max_length=255, unique=True)
    detail = models.TextField(max_length=1000, blank=True)
    credit_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)


    class Meta:
        ordering = ['created_at']


    def __str__(self) -> str:
        return self.name



class InitialCreditBalance(UpdatedCreatedBy, YearClosureUtilClass):
    party = models.ForeignKey(Party, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    date = models.DateField(default=now)
    notes = models.TextField(blank=True)
    year_closure = models.ForeignKey('year_closure.ClosurePeriod', on_delete=models.CASCADE, null=True, related_name="ycicb")

    class Meta:
        ordering = ['created_at']


    def __str__(self) -> str:
        return f"{self.party.name} - {self.amount}"



FILTERS = lambda date_field_name, party_field_name, start_date_obj, end_date_obj, client_ids: [ 
    Q(**{f"{date_field_name}__range": [start_date_obj, end_date_obj]}) if start_date_obj and end_date_obj else Q(),
    Q(**{f"{party_field_name}__in": client_ids}) if client_ids else Q() 
]
MONEY = DecimalField(max_digits=20, decimal_places=2)
ZERO = Value(Decimal("0"), output_field=MONEY)

year_closure_instance_id = settings.CLOSEURE_PERIOD_INSTANCE_ID
is_active_only = settings.ACTIVE_ONLY

class PartySubModelsUtils:
    def __init__(self):
        self.manager = None
        if      is_active_only:             self.manager = 'active_objects'
        elif    year_closure_instance_id:   self.manager = 'specific_objects'
        else:                               self.manager = 'objects'

    @staticmethod
    def __get_manager(model, name=None):
        """Return model.<name> if given, otherwise the model's default manager."""
        if not name:
            return model._default_manager
        try:
            return getattr(model, name)
        except AttributeError:
            raise ValueError(f"{model.__name__} has no manager '{name}'")

    @staticmethod
    def __sub_models_accessor_config(start_date_obj, end_date_obj, party_field_name, is_confirmed_transactions_only):
        rb = Q(repository_permit=True) if is_confirmed_transactions_only else Q()
        ps = Q(status=2) if is_confirmed_transactions_only else Q()
        ms = Q(maintenance_date__isnull=False) if is_confirmed_transactions_only else Q()
        ms2 = Q(date_out__isnull=False) if is_confirmed_transactions_only else Q()
        ss = Q(status="approved") if is_confirmed_transactions_only else Q()
        
        return {
            "initialcreditbalance":     { "field": 'amount',       "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("date", "party", start_date_obj, end_date_obj, party_field_name) ]},
            "purchaseinvoices":         { "field": 'total_amount', "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("issue_date", "owner", start_date_obj, end_date_obj, party_field_name), rb]},
            "salesinvoice":             { "field": 'total_amount', "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("issue_date", "owner", start_date_obj, end_date_obj, party_field_name), rb]},
            "returninvoice":            { "field": 'total_amount', "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("issue_date", "owner", start_date_obj, end_date_obj, party_field_name), rb]},
            "maintenance_transactions": { "field": 'cost',         "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("date_in", "client", start_date_obj, end_date_obj, party_field_name), ms, ms2]},
            "debtsettlement":           { "field": 'amount',       "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("date", "owner", start_date_obj, end_date_obj, party_field_name), ss]},
            "payment2":                 { "field": 'amount',       "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("date", "owner", start_date_obj, end_date_obj, party_field_name), ps]},
            "reversepayment2":          { "field": 'amount',       "manager": PartySubModelsUtils().manager, 'filters': [ *FILTERS("date", "owner", start_date_obj, end_date_obj, party_field_name), ps]},
        }

    def _get_total_credit(self, start_date_obj, end_date_obj, client_ids, is_confirmed_transactions_only, options=1):
        rels = {}
        for rel in Party._meta.related_objects:
            rels[rel.name] = rel
            if rel.get_accessor_name():
                rels[rel.get_accessor_name()] = rel
        
        annotations = {}
        stats = defaultdict(dict)   # {party_id: {key: {"total": Decimal, "count": int}}}
        config = self.__sub_models_accessor_config(start_date_obj, end_date_obj, client_ids, is_confirmed_transactions_only)
        for key, cfg in config.items():
            try:
                rel = rels[key]
            except KeyError:
                raise ValueError(f"'{key}' is not a reverse relation of Party")

            if options == 1:
                fk = rel.field.name
                rows = (
                    self.__get_manager(rel.related_model, cfg.get("manager"))
                    .filter(**{f"{fk}__in": client_ids})
                    .filter(*cfg["filters"])
                    .order_by()
                    .values(fk)
                    .annotate(
                        total=Sum(cfg["field"], output_field=MONEY),
                        count=Count("pk"),
                    )
                )
                for r in rows:
                    stats[r[fk]][key] = {"total": r["total"], "count": r["count"]}
            elif options == 2:
                    fk_name = rel.field.name
                    sub = (
                        self.__get_manager(rel.related_model, cfg.get("manager"))
                        .filter(**{fk_name: OuterRef("pk")})
                        .filter(*cfg["filters"])
                        .order_by()
                        .values(fk_name)
                        .annotate(total=Sum(cfg["field"], output_field=MONEY))
                        .values("total")
                    )
                    annotations[f"{key}_total"] = Coalesce(
                        Subquery(sub, output_field=MONEY), ZERO
                    )

        if options == 1:            
            return stats
        elif options == 2:
            return Party.objects.filter(Q(pk__in=client_ids) if client_ids else Q()).annotate(**annotations)

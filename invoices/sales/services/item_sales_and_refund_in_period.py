from invoices.sales.models import SalesInvoiceItem, ReturnInvoiceItem
from django.db.models import Sum
from decimal import Decimal
from rest_framework.response import Response



# ...existing code...
def get_sold_and_refund_items_totals_withen_period(date_from, date_to):
    """
    Return list of dicts with aggregated sold, returned and net totals per item+repository
    within [date_from, date_to]. Each dict:
      {
        "item_id": int,
        "item_repr": str or None,
        "repository_id": int or None,
        "quantity_sold": Decimal,
        "quantity_returned": Decimal,
        "net_quantity": Decimal,
        "total_sold": Decimal,
        "total_returned": Decimal,
        "net_total": Decimal,
      }
    """
    # helper to build filter kwargs trying common relation names
    def date_filter_kwargs(model):
        for key in ("invoice__issue_date", "date"):
            try:
                # test by building kwargs; we don't access DB here, just return candidate
                return {f"{key}__gte": date_from, f"{key}__lte": date_to}
            except Exception:
                continue
        # fallback (will likely raise later if wrong)
        return {"invoice__date__gte": date_from, "invoice__date__lte": date_to}

    # aggregate sales
    sold_qs = SalesInvoiceItem.objects.filter(**date_filter_kwargs(SalesInvoiceItem))
    sold_values = sold_qs.values(
        "item_id", 
        "item__id", 
        "item__name", 
        "repository_id"
    ).annotate(
        quantity_sold=Sum("quantity"),
        total_sold=Sum("total"),
    )

    # aggregate returns
    return_qs = ReturnInvoiceItem.objects.filter(**date_filter_kwargs(ReturnInvoiceItem))
    return_values = return_qs.values(
        "item_id", 
        "item__id", 
        "item__name", 
        "repository_id"
    ).annotate(
        quantity_returned=Sum("quantity"),
        total_returned=Sum("total"),
    )

    # merge results by (item_id, repository_id)
    results_map = {}
    for s in sold_values:
        key = (s.get("item_id"), s.get("repository_id"))
        results_map[key] = {
            "item_id": s.get("item_id"),
            "item_repr": s.get("item__name") or None,
            "repository_id": s.get("repository_id"),
            "quantity_sold": s.get("quantity_sold") or Decimal("0"),
            "quantity_returned": Decimal("0"),
            "net_quantity": Decimal("0"),
            "total_sold": s.get("total_sold") or Decimal("0"),
            "total_returned": Decimal("0"),
            "net_total": Decimal("0"),
        }

    for r in return_values:
        key = (r.get("item_id"), r.get("repository_id"))
        entry = results_map.get(key)
        qty_ret = r.get("quantity_returned") or Decimal("0")
        tot_ret = r.get("total_returned") or Decimal("0")
        if entry:
            entry["quantity_returned"] = qty_ret
            entry["total_returned"] = tot_ret
        else:
            results_map[key] = {
                "item_id": r.get("item_id"),
                "item_repr": r.get("item__name") or None,
                "repository_id": r.get("repository_id"),
                "quantity_sold": Decimal("0"),
                "quantity_returned": qty_ret,
                "net_quantity": Decimal("0"),
                "total_sold": Decimal("0"),
                "total_returned": tot_ret,
                "net_total": Decimal("0"),
            }

    # compute net values and return as list
    out = []
    for v in results_map.values():
        v["net_quantity"] = (v["quantity_sold"] or Decimal("0")) - (v["quantity_returned"] or Decimal("0"))
        v["net_total"] = (v["total_sold"] or Decimal("0")) - (v["total_returned"] or Decimal("0"))
        out.append(v)

    return out

def get_sold_and_items_totals_withen_period_as_http_response(from_date, to_date):
    return Response(get_sold_and_refund_items_totals_withen_period(from_date, to_date))

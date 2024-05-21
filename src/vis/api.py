from datetime import date
from typing import List, Optional, Literal

from ninja import Router, Query
from ninja.security import django_auth
from ninja.pagination import paginate
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt

from main.schema import (
    UnprocessableContentSchema,
    ForbiddenSchema,
    NotFoundSchema,
)
from users.auth import UidKeyAuth
from registry.models import Model
from registry.pagination import PagesPagination
from .models import ResultsProbForecast, GeoMacroSaude
from .schema import ResultsProbForecastSchema, ResultsProbForecastFilterSchema


router = Router()
uidkey = UidKeyAuth()


@router.get(
    "/results-prob-forecast/",
    response={
        200: List[ResultsProbForecastSchema],
        422: UnprocessableContentSchema,
    },
    auth=django_auth,
    include_in_schema=True,
)
@paginate(PagesPagination)
def list_results_prob_forecast(
    request,
    disease: Optional[Literal["dengue", "zika", "chik"]],
    filters: ResultsProbForecastFilterSchema = Query(...),
    **kwargs,
):
    if disease and disease not in ["dengue", "zika", "chik"]:
        return 422, {
            "message": "Incorrect disease, options: ['dengue', 'zika', 'chik']"
        }

    try:
        date.fromisoformat(str(filters.date))
    except ValueError:
        return 422, {
            "message": "Incorrect date format, please use isoformat: YYYY-MM-dd"
        }

    objs = filters.filter(
        ResultsProbForecast.objects.filter(disease=disease)
    ).order_by("-date")

    res = [
        dict(
            disease=obj.disease,
            date=obj.date,
            geocode=int(obj.geocode.geocode),
            lower_2_5=obj.lower_2_5,
            lower_25=obj.lower_25,
            forecast=obj.forecast,
            upper_75=obj.upper_75,
            upper_97_5=obj.upper_97_5,
            prob_high=obj.prob_high,
            prob_low=obj.prob_low,
            high_threshold=obj.high_threshold,
            low_threshold=obj.low_threshold,
            high_incidence_threshold=obj.high_incidence_threshold,
            low_incidence_threshold=obj.low_incidence_threshold,
        )
        for obj in objs
    ]

    return res


@router.post(
    "/results-prob-forecast/",
    response={
        201: ResultsProbForecastSchema,
        403: ForbiddenSchema,
        404: NotFoundSchema,
        422: UnprocessableContentSchema,
    },
    auth=uidkey,
    include_in_schema=True,
)
@csrf_exempt
def post_results_prob_forecast(request, payload: ResultsProbForecastSchema):
    if payload.disease not in ["dengue", "zika", "chik"]:
        return 422, {
            "message": "Incorrect disease, options: ['dengue', 'zika', 'chik']"
        }

    try:
        date.fromisoformat(str(payload.date))
    except ValueError:
        return 422, {
            "message": "Incorrect date format, please use isoformat: YYYY-MM-dd"
        }

    data = payload.dict()
    try:
        data["geocode"] = GeoMacroSaude.objects.get(pk=data["geocode"])
    except GeoMacroSaude.DoesNotExist:
        return 404, {"message": f"Unknown geocode {data['geocode']}"}

    try:
        data["model"] = Model.objects.get(pk=data["model"])
        del data["model"]
    except GeoMacroSaude.DoesNotExist:
        return 404, {"message": f"Unknown geocode {data['geocode']}"}

    obj = ResultsProbForecast(**data)

    try:
        obj.save()
    except IntegrityError:
        return 403, {
            "message": (
                "Forecast Result for this date and geocode already inserted"
            )
        }

    data["geocode"] = data["geocode"].geocode

    return 201, data

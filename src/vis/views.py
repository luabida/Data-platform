import os
import json
import geopandas as gpd
from typing import Union
from itertools import cycle

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.contrib import messages

from registry.models import Model, Prediction
from main.api import get_municipality_info
from .dash.charts import line_charts_by_geocode
from .home.vis_charts import uf_ibge_mapping


class DashboardView(View):
    template_name = "vis/dashboard.html"

    def get(self, request):
        context = {}

        context["selectedDisease"] = None
        context["selectedTimeResolution"] = None
        context["selectedADMLevel"] = None
        context["selectedSpatial"] = None
        context["selectedTemporal"] = None
        context["selectedOutputFormat"] = None
        context["selectedGeocode"] = None

        selected_model = request.GET.get("model", None)
        selected_prediction = request.GET.get("predict", None)

        if selected_model:
            model = Model.objects.get(pk=selected_model)
            context["selectedDisease"] = model.disease or None
            context["selectedTimeResolution"] = model.time_resolution or None
            context["selectedADMLevel"] = model.ADM_level
            context["selectedSpatial"] = model.spatial
            context["selectedTemporal"] = model.temporal
            context["selectedOutputFormat"] = model.categorical
            context["selectedPredictions"] = None

        if selected_prediction:
            prediction = Prediction.objects.get(pk=selected_prediction)
            context["selectedDisease"] = prediction.model.disease or None
            context["selectedTimeResolution"] = (
                prediction.model.time_resolution or None
            )
            context["selectedADMLevel"] = prediction.model.ADM_level
            context["selectedSpatial"] = prediction.model.spatial
            context["selectedTemporal"] = prediction.model.temporal
            context["selectedOutputFormat"] = prediction.model.categorical
            context["selectedGeocode"] = prediction.adm_2_geocode or None
            context["selectedPredictions"] = prediction.id or None

        if context["selectedDisease"] == "chikungunya":
            context["selectedDisease"] = "chik"

        print(context)

        models = Model.objects.all()
        predictions = Prediction.objects.filter(visualizable=True)

        city_names_w_uf = []
        for geocode in predictions.values_list("adm_2_geocode", flat=True):
            if geocode:
                _, info = get_municipality_info(request, geocode)
                city_names_w_uf.append(f"{info['municipio']} - {info['uf']}")

        predictions_data = list(
            zip(
                list(predictions.values_list("id", flat=True)),
                list(predictions.values_list("model__name", flat=True)),
                list(predictions.values_list("metadata", flat=True)),
                city_names_w_uf,
            )
        )

        context["predictions"] = predictions_data

        model_types = set()
        output_formats = set()
        for model in models:
            if model.categorical:
                output_formats.add("C")
            else:
                output_formats.add("Q")

            if model.spatial:
                model_types.add("spatial")

            if model.temporal:
                model_types.add("temporal")

        context["model_types"] = list(model_types)
        context["output_formats"] = list(output_formats)

        context["diseases"] = list(
            set(models.values_list("disease", flat=True))
        )

        context["adm_levels"] = list(
            set(models.values_list("ADM_level", flat=True))
        )

        context["time_resolutions"] = list(
            set(models.values_list("time_resolution", flat=True))
        )

        adm_2_geocodes = set(
            predictions.values_list("adm_2_geocode", flat=True)
        )

        geocode_cities = set()
        municipios_file = os.path.join("static", "data/geo/BR/municipios.json")
        if os.path.isfile(municipios_file):
            uf_codes = dict()
            for uf, info in uf_ibge_mapping.items():
                uf_codes[int(info["code"])] = uf

            with open(municipios_file, "rb") as f:
                geocodes = json.load(f)

            for geocode in geocodes:
                if int(geocode) in adm_2_geocodes:
                    data = geocodes[geocode]
                    geocode_cities.add(
                        (
                            geocode,
                            data["municipio"],
                            uf_codes[int(data["codigo_uf"])],
                        )
                    )

        context["adm_2_geocodes"] = list(geocode_cities)

        return render(request, self.template_name, context)


class LineChartsView(View):
    template_name = "vis/charts/line-charts.html"

    def get(self, request):
        context = {}

        prediction_ids = request.GET.getlist("predict")

        predictions: set[Prediction] = set()
        colors = cycle(
            [
                "#A6BCD4",
                "#FAC28C",
                "#F2ABAB",
                "#B9DBD9",
                "#AAD1A5",
                "#F7E59D",
                "#D9BCD1",
                "#FFCED3",
                "#CEBAAE",
            ]
        )

        if not prediction_ids:
            # Show "Please select Predictions"
            return render(request, "vis/errors/no-prediction.html", context)

        if prediction_ids:
            for id in prediction_ids:
                predict = get_object_or_404(Prediction, pk=id)
                predictions.add(predict)

        ids = []
        infos = []
        for prediction in predictions:
            info = {}
            ids.append(prediction.id)
            info["model"] = f"{prediction.model.id} - {prediction.model.name}"
            info["prediction_id"] = prediction.id
            info["disease"] = prediction.model.disease.capitalize()
            if prediction.adm_2_geocode and prediction.model.ADM_level == 2:
                geocode = prediction.adm_2_geocode
                geocode_info = json.loads(
                    get_geocode_info(request, geocode).content
                )
                info["locality"] = geocode_info["municipio"]
            else:
                info["locality"] = "BR"  # TODO
            info["prediction_date"] = prediction.predict_date
            info["color"] = next(colors)
            infos.append(info)

        context["prediction_ids"] = ids
        context["prediction_infos"] = infos

        try:
            line_chart = line_charts_by_geocode(
                title="Forecast of dengue new cases",
                predictions_ids=ids,
                disease="dengue",
                width=450,
                request=request,
            )
            line_chart = line_chart.to_html().replace(
                "</head>",
                "<style>#vis.vega-embed {width: 100%;}</style></head>",
            )
            context["line_chart"] = line_chart
        except Exception as e:
            # TODO: ADD HERE ERRORING PAGES TO BE RETURNED
            context["error"] = e

        return render(request, self.template_name, context)


class GeoPackageView(View):
    template_name = "vis/charts/geopackage.html"

    def post(self, request):
        if not (request.user.is_authenticated and request.user.is_superuser):
            return redirect("home")

        try:
            data = json.loads(request.body)
            file_path = data.get("file_path")
            context = {}
            if file_path:
                try:
                    df = gpd.read_file(file_path)
                    context["df"] = df.to_html()
                    print(context["df"])
                    return render(request, self.template_name, context)
                except Exception:
                    messages.error(request, "Error reading gpkg file")
                    return HttpResponseBadRequest("Error reading gpkg file")

        except json.JSONDecodeError:
            messages.error(request, "Error decoding JSON data")
            return HttpResponseBadRequest()

        return render(request, self.template_name, context)

    def get(self, request):
        if not (request.user.is_authenticated and request.user.is_superuser):
            return redirect("home")


def get_model_selector_item(request, model_id):
    try:
        model = Model.objects.get(pk=model_id)
        data = {
            "name": model.name,
            "description": model.description,
        }
        return JsonResponse(data)
    except Model.DoesNotExist:
        return JsonResponse({"error": "Model not found"}, status=404)


def get_prediction_selector_item(request, prediction_id):
    try:
        prediction = Prediction.objects.get(pk=prediction_id)
        data = {
            "model_id": prediction.model.id,
            "description": prediction.description,
        }
        return JsonResponse(data)
    except Prediction.DoesNotExist:
        return JsonResponse({"error": "Prediction not found"}, status=404)


def get_geocode_info(request, geocode: Union[str, int]):
    geocode = str(geocode)
    municipios_file = os.path.join("static", "data/geo/BR/municipios.json")

    if os.path.isfile(municipios_file):
        with open(municipios_file, "r") as f:
            geocodes = json.load(f)

        data = geocodes[geocode]
        uf_code = data["codigo_uf"]

        for uf, info in uf_ibge_mapping.items():
            if str(info["code"]) == str(uf_code):
                data["uf"] = uf

        return JsonResponse(data)
    else:
        return JsonResponse({"error": "Geocode not found"}, status=404)

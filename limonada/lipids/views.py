from django.shortcuts import render
import json
import requests

from .models import PoCLipid, top_example


# Create your views here.
def poc_lipid(request):
    lipid = PoCLipid()

    lm_response = requests.get(
        "http://www.lipidmaps.org/rest/compound/lm_id/%s/all/json" % lipid.lmid)

    lm_data_raw = lm_response.json()
    lm_data = {}
    if lm_response.status_code == 200:
        for key in ["pubchem_cid", "name", "sys_name", "main_class", "sub_class", "core"]:
            lm_data[key] = lm_data_raw[key]

    pubchem_data = {}
    try:
        pubchem_response = requests.get(
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/%s/JSON/" % lm_data[
                "pubchem_cid"])
        pubchem_data_raw = pubchem_response.json()["Record"]
    except KeyError:
        pass
    else:
        if pubchem_response.status_code == 200:
            pubchem_data["IUPACName"] = \
                pubchem_data_raw["Section"][2]["Section"][1]["Section"][0]["Information"][0][
                    'StringValue']
            pubchem_data["Formula"] = pubchem_data_raw["Section"][2]["Section"][2]["Information"][0]["StringValue"]
            pubchem_data["Names"] = pubchem_data_raw["Section"][2]["Section"][4]["Section"][0]["Information"][0]["StringValueList"]
            pubchem_data["Mass"] = "%.2f %s" % (pubchem_data_raw["Section"][3]["Section"][0]["Section"][0]["Information"][0]["NumValue"], pubchem_data_raw["Section"][3]["Section"][0]["Section"][0]["Information"][0]["ValueUnit"])

    context = {
        "lipid": lipid,
        "lm_data": lm_data,
        "pubchem_data": pubchem_data,
    }

    return render(request, "lipids/poc.html", context=context)


def poc_lipid_top(request):
    top_example.parent = PoCLipid()
    context = {"lipid": top_example}
    return render(request, "lipids/poc_top.html", context=context)

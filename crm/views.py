from django.shortcuts import render


def company_list(request):
    return render(request, "crm/company_list.html", {"section": "companies"})


def candidate_list(request):
    return render(request, "crm/candidate_list.html", {"section": "candidates"})


def pipeline(request):
    return render(request, "crm/pipeline.html", {"section": "pipeline"})

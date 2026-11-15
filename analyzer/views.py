from django.shortcuts import render
from .forms import WebsiteAnalysisForm
from .services import analyze_website, analyze_google_pagespeed

def home(request):
    form = WebsiteAnalysisForm(request.POST or None)

    report = None
    google_report = None

    if request.method == "POST" and form.is_valid():
        url = form.cleaned_data["url"]

        report = analyze_website(url)

        if report["success"]:
            google_report = analyze_google_pagespeed(url)

    return render(request, "analyzer/home.html", {
        "form": form,
        "report": report,
        "google_report": google_report
    })
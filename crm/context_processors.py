from .models import Candidate, Company


def _distinct_locations():
    locations = set(
        Company.objects.exclude(location="").values_list("location", flat=True)
    ) | set(Candidate.objects.exclude(location="").values_list("location", flat=True))
    return sorted(locations, key=str.casefold)


def location_options(request):
    """Locations for the `_location_datalist.html` autocomplete partial.

    Exposed as a callable: the template engine only invokes it when a
    template actually renders `location_options`, so pages without a
    location input never run the query.
    """
    return {"location_options": _distinct_locations}

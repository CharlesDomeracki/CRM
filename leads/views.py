from urllib.parse import quote, urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .geo import geocode_city_state, geocode_postalcode, haversine_miles
from .hours_fetch import FIELD_BY_DAY, fetch_hours_from_url
from .models import Lead

PAGE_SIZE = 100
MAX_RADIUS_STOPS = 500


@login_required
def lead_list(request):
    leads = Lead.objects.all()

    query = request.GET.get("q", "").strip()
    if query:
        leads = leads.filter(name__icontains=query) | leads.filter(
            city__icontains=query
        ) | leads.filter(state__icontains=query)

    statuses_selected = [s for s in request.GET.getlist("status") if s.strip()]
    if statuses_selected:
        leads = leads.filter(status__in=statuses_selected)

    states_selected = [s for s in request.GET.getlist("state") if s.strip()]
    if states_selected:
        leads = leads.filter(state__in=states_selected)

    cities_selected = [c for c in request.GET.getlist("city") if c.strip()]
    if cities_selected:
        leads = leads.filter(city__in=cities_selected)

    categories_selected = [c for c in request.GET.getlist("category") if c.strip()]
    if categories_selected:
        leads = leads.filter(primary_category_name__in=categories_selected)

    ratings_selected = [r for r in request.GET.getlist("rating") if r.strip()]
    if ratings_selected:
        leads = leads.filter(conversion_rating__in=ratings_selected)

    has_email = request.GET.get("has_email", "").strip()
    if has_email == "yes":
        leads = leads.exclude(email="")
    elif has_email == "no":
        leads = leads.filter(email="")

    has_website = request.GET.get("has_website", "").strip()
    if has_website == "yes":
        leads = leads.exclude(url="")
    elif has_website == "no":
        leads = leads.filter(url="")

    has_phone = request.GET.get("has_phone", "").strip()
    if has_phone == "yes":
        leads = leads.exclude(phone="")
    elif has_phone == "no":
        leads = leads.filter(phone="")

    in_mall = request.GET.get("in_mall", "").strip()
    if in_mall == "yes":
        leads = leads.filter(in_mall=True)
    elif in_mall == "no":
        leads = leads.filter(in_mall=False)

    has_hours = request.GET.get("has_hours", "").strip()
    hour_fields = ["monday_hours", "tuesday_hours", "wednesday_hours", "thursday_hours", "friday_hours", "saturday_hours", "sunday_hours"]
    if has_hours == "yes":
        q = Q()
        for f in hour_fields:
            q |= ~Q(**{f: ""})
        leads = leads.filter(q)
    elif has_hours == "no":
        leads = leads.filter(**{f: "" for f in hour_fields})

    sort = request.GET.get("sort", "").strip()
    if sort == "rating":
        leads = leads.order_by("star_count")
    elif sort == "-rating":
        leads = leads.order_by("-star_count")
    else:
        leads = leads.order_by("state", "city")

    states = (
        Lead.objects.exclude(state="")
        .values("state")
        .annotate(count=Count("id"))
        .order_by("state")
    )
    cities_by_state = {}
    if states_selected:
        state_city_counts = (
            Lead.objects.filter(state__in=states_selected)
            .exclude(city="")
            .values("state", "city")
            .annotate(count=Count("id"))
            .order_by("state", "city")
        )
        for row in state_city_counts:
            cities_by_state.setdefault(row["state"], []).append((row["city"], row["count"]))
    categories = (
        Lead.objects.order_by("primary_category_name")
        .values_list("primary_category_name", flat=True)
        .distinct()
    )

    paginator = Paginator(leads, PAGE_SIZE)
    page_number = request.GET.get("page", "1")
    page_obj = paginator.get_page(page_number)

    detail_link_qs = urlencode(
        [("q", query), ("sort", sort), ("page", page_obj.number), ("has_email", has_email), ("has_website", has_website), ("has_phone", has_phone), ("in_mall", in_mall), ("has_hours", has_hours)]
        + [("status_filter", s) for s in statuses_selected]
        + [("state_filter", s) for s in states_selected]
        + [("city_filter", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
    )
    filters_qs = urlencode(
        [("q", query), ("has_email", has_email), ("has_website", has_website), ("has_phone", has_phone), ("in_mall", in_mall), ("has_hours", has_hours)]
        + [("status", s) for s in statuses_selected]
        + [("state", s) for s in states_selected]
        + [("city", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
    )
    pagination_qs = urlencode(
        [("q", query), ("sort", sort), ("has_email", has_email), ("has_website", has_website), ("has_phone", has_phone), ("in_mall", in_mall), ("has_hours", has_hours)]
        + [("status", s) for s in statuses_selected]
        + [("state", s) for s in states_selected]
        + [("city", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
    )
    rating_sort_toggle = "-rating" if sort == "rating" else "rating"
    is_partial = request.headers.get("HX-Request") == "true"

    return render(
        request,
        "leads/_lead_list_results.html" if is_partial else "leads/lead_list.html",
        {
            "leads": page_obj,
            "page_obj": page_obj,
            "pagination_qs": pagination_qs,
            "total_count": paginator.count,
            "query": query,
            "statuses_selected": statuses_selected,
            "states_selected": states_selected,
            "cities_selected": cities_selected,
            "categories_selected": categories_selected,
            "ratings_selected": ratings_selected,
            "has_email": has_email,
            "has_website": has_website,
            "has_phone": has_phone,
            "in_mall": in_mall,
            "has_hours": has_hours,
            "states": [(row["state"], row["count"]) for row in states],
            "cities_by_state": cities_by_state,
            "categories": [c for c in categories if c],
            "status_choices": Lead.STATUS_CHOICES,
            "rating_choices": Lead.CONVERSION_RATING_CHOICES,
            "detail_link_qs": detail_link_qs,
            "filters_qs": filters_qs,
            "sort": sort,
            "rating_sort_toggle": rating_sort_toggle,
            "is_partial": is_partial,
        },
    )


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    params = request.POST if request.method == "POST" else request.GET
    categories_selected = [c for c in params.getlist("category") if c.strip()]
    statuses_selected = [s for s in params.getlist("status_filter") if s.strip()]
    states_selected = [s for s in params.getlist("state_filter") if s.strip()]
    cities_selected = [c for c in params.getlist("city_filter") if c.strip()]
    ratings_selected = [r for r in params.getlist("rating") if r.strip()]
    filter_params = {
        list_key: params[form_key]
        for form_key, list_key in (
            ("q", "q"),
            ("sort", "sort"),
            ("page", "page"),
            ("has_email", "has_email"),
            ("has_website", "has_website"),
            ("has_phone", "has_phone"),
        )
        if params.get(form_key)
    }
    filter_qs = urlencode(
        list(filter_params.items())
        + [("status", s) for s in statuses_selected]
        + [("state", s) for s in states_selected]
        + [("city", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
    )
    return_to = params.get("return_to", "")
    if not return_to.startswith("/") or return_to.startswith("//"):
        return_to = ""

    if request.method == "POST":
        lead.name = request.POST.get("name", "").strip()
        lead.address = request.POST.get("address", "").strip()
        lead.city = request.POST.get("city", "").strip()
        lead.state = request.POST.get("state", "").strip()
        lead.zip = request.POST.get("zip", "").strip()
        lead.country = request.POST.get("country", "").strip()
        lead.phone = request.POST.get("phone", "").strip()
        lead.email = request.POST.get("email", "").strip()
        lead.url = request.POST.get("url", "").strip()
        lead.primary_category_name = request.POST.get("primary_category_name", "").strip()
        lead.category_name = request.POST.get("category_name", "").strip()
        lead.status = request.POST.get("status", lead.status)
        lead.conversion_rating = request.POST.get("conversion_rating", lead.conversion_rating)
        lead.notes = request.POST.get("notes", lead.notes)
        lead.contact_date = request.POST.get("contact_date", "").strip() or None
        lead.followup_date = request.POST.get("followup_date", "").strip() or None
        lead.monday_hours = request.POST.get("monday_hours", "").strip()
        lead.tuesday_hours = request.POST.get("tuesday_hours", "").strip()
        lead.wednesday_hours = request.POST.get("wednesday_hours", "").strip()
        lead.thursday_hours = request.POST.get("thursday_hours", "").strip()
        lead.friday_hours = request.POST.get("friday_hours", "").strip()
        lead.saturday_hours = request.POST.get("saturday_hours", "").strip()
        lead.sunday_hours = request.POST.get("sunday_hours", "").strip()
        lead.in_mall = request.POST.get("in_mall") == "on"
        lead.facebook_link = request.POST.get("facebook_link", "").strip()
        lead.instagram_link = request.POST.get("instagram_link", "").strip()
        lead.twitter_link = request.POST.get("twitter_link", "").strip()
        lead.whatsapp_link = request.POST.get("whatsapp_link", "").strip()
        lead.linkedin_link = request.POST.get("linkedin_link", "").strip()
        lead.youtube_link = request.POST.get("youtube_link", "").strip()

        errors = []
        if not lead.name:
            errors.append("Name is required.")

        if not errors:
            lead.save()
            if return_to:
                return redirect(return_to)
            list_url = reverse("leads:list")
            if filter_qs:
                list_url += f"?{filter_qs}"
            return redirect(list_url)

        return render(
            request,
            "leads/lead_detail.html",
            {
                "lead": lead,
                "errors": errors,
                "filter_qs": filter_qs,
                "return_to": return_to,
                "q": params.get("q", ""),
                "statuses_selected": statuses_selected,
                "states_selected": states_selected,
                "cities_selected": cities_selected,
                "categories_selected": categories_selected,
                "ratings_selected": ratings_selected,
                "rating_choices": Lead.CONVERSION_RATING_CHOICES,
                "sort": params.get("sort", ""),
                "page": params.get("page", ""),
                "has_email": params.get("has_email", ""),
                "has_website": params.get("has_website", ""),
                "has_phone": params.get("has_phone", ""),
                "months_range": range(1, 13),
            },
        )

    return render(
        request,
        "leads/lead_detail.html",
        {
            "lead": lead,
            "errors": [],
            "filter_qs": filter_qs,
            "return_to": return_to,
            "q": params.get("q", ""),
            "statuses_selected": statuses_selected,
            "states_selected": states_selected,
            "cities_selected": cities_selected,
            "categories_selected": categories_selected,
            "ratings_selected": ratings_selected,
            "rating_choices": Lead.CONVERSION_RATING_CHOICES,
            "sort": params.get("sort", ""),
            "page": params.get("page", ""),
            "has_email": params.get("has_email", ""),
            "has_website": params.get("has_website", ""),
            "has_phone": params.get("has_phone", ""),
            "months_range": range(1, 13),
        },
    )


@login_required
def lead_fetch_hours(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    return_to = request.POST.get("return_to", "")
    if not return_to.startswith("/") or return_to.startswith("//"):
        return_to = ""
    redirect_target = return_to or reverse("leads:detail", kwargs={"pk": lead.pk})

    if request.method != "POST":
        return redirect(redirect_target)

    hours = fetch_hours_from_url(lead.url)
    source = "the website" if hours else ""
    if not hours and lead.facebook_link:
        hours = fetch_hours_from_url(lead.facebook_link)
        source = "Facebook" if hours else source

    if hours:
        for day, field in FIELD_BY_DAY.items():
            if day in hours:
                setattr(lead, field, hours[day])
        lead.save()
        messages.success(request, f"Store hours updated from {source}.")
    else:
        messages.warning(
            request, "Couldn't find structured hours on the website or Facebook page."
        )

    return redirect(redirect_target)


@login_required
def lead_route(request):
    lead_ids = [pk for pk in request.GET.getlist("lead_ids") if pk.strip()]
    leads = list(Lead.objects.filter(pk__in=lead_ids))
    leads.sort(key=lambda lead: lead_ids.index(str(lead.pk)))

    stops = []
    for lead in leads:
        full_address = lead.address or ", ".join(
            part for part in (lead.city, lead.state, lead.zip) if part
        )
        stops.append({"lead": lead, "full_address": full_address})

    start_address = request.GET.get("start", "").strip()

    maps_url = ""
    addresses = [stop["full_address"] for stop in stops if stop["full_address"]]
    if start_address:
        addresses = [start_address] + addresses
    if addresses:
        maps_url = "https://www.google.com/maps/dir/" + "/".join(
            quote(addr) for addr in addresses
        )

    back_qs = request.GET.get("back", "")
    route_url = request.get_full_path()

    return render(
        request,
        "leads/lead_route.html",
        {
            "stops": stops,
            "maps_url": maps_url,
            "back_qs": back_qs,
            "start_address": start_address,
            "lead_ids": lead_ids,
            "route_url": route_url,
        },
    )


@login_required
def lead_route_by_location(request):
    city = request.GET.get("city", "").strip()
    state = request.GET.get("state", "").strip()
    zip_code = request.GET.get("zip", "").strip()
    radius_raw = request.GET.get("radius", "").strip()

    if zip_code:
        location_label = zip_code
    elif city and state:
        location_label = f"{city}, {state}"
    else:
        messages.warning(
            request, "Enter a city and state, or a zip code, to build a route by location."
        )
        return redirect("leads:list")

    try:
        radius = float(radius_raw)
        if radius <= 0:
            raise ValueError
    except ValueError:
        messages.warning(request, "Enter a valid mileage radius greater than 0.")
        return redirect("leads:list")

    max_stops_raw = request.GET.get("max_stops", "").strip()
    if max_stops_raw:
        try:
            max_stops = int(max_stops_raw)
            if max_stops <= 0:
                raise ValueError
        except ValueError:
            messages.warning(request, "Enter a valid max stops value greater than 0.")
            return redirect("leads:list")
        max_stops = min(max_stops, MAX_RADIUS_STOPS)
    else:
        max_stops = MAX_RADIUS_STOPS

    origin = geocode_postalcode(zip_code) if zip_code else geocode_city_state(city, state)
    if origin is None:
        messages.warning(
            request, f"Couldn't find a location for \"{location_label}\". Try a different spelling."
        )
        return redirect("leads:list")
    origin_lat, origin_lng = origin

    candidates = Lead.objects.exclude(lat__isnull=True).exclude(lng__isnull=True)
    in_range = []
    for lead in candidates:
        distance = haversine_miles(origin_lat, origin_lng, lead.lat, lead.lng)
        if distance <= radius:
            in_range.append((distance, lead))
    in_range.sort(key=lambda pair: pair[0])

    if not in_range:
        messages.warning(
            request, f"No leads found within {radius:g} miles of {location_label}."
        )
        return redirect("leads:list")

    truncated = len(in_range) > max_stops
    in_range = in_range[:max_stops]

    if truncated:
        messages.success(
            request,
            f"Found {len(in_range)}+ leads within {radius:g} miles "
            f"(showing the closest {max_stops}).",
        )
    else:
        messages.success(
            request, f"Found {len(in_range)} lead(s) within {radius:g} miles of {location_label}."
        )

    params = [("lead_ids", str(lead.pk)) for _, lead in in_range]
    params.append(("start", location_label))
    return redirect(f"{reverse('leads:route')}?{urlencode(params)}")


@login_required
def lead_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        errors = []
        if not name:
            errors.append("Name is required.")

        if not errors:
            lead = Lead.objects.create(
                name=name,
                address=request.POST.get("address", "").strip(),
                phone=request.POST.get("phone", "").strip(),
                email=request.POST.get("email", "").strip(),
                url=request.POST.get("url", "").strip(),
                city=request.POST.get("city", "").strip(),
                state=request.POST.get("state", "").strip(),
                zip=request.POST.get("zip", "").strip(),
                primary_category_name=request.POST.get("primary_category_name", "").strip(),
                status=request.POST.get("status", "new"),
                conversion_rating=request.POST.get("conversion_rating", "not_contacted"),
                notes=request.POST.get("notes", "").strip(),
                in_mall=request.POST.get("in_mall") == "on",
            )
            return redirect("leads:detail", pk=lead.pk)
        return render(
            request,
            "leads/lead_form.html",
            {
                "errors": errors,
                "form_data": request.POST,
                "status_choices": Lead.STATUS_CHOICES,
                "rating_choices": Lead.CONVERSION_RATING_CHOICES,
            },
        )

    return render(
        request,
        "leads/lead_form.html",
        {
            "errors": [],
            "form_data": {},
            "status_choices": Lead.STATUS_CHOICES,
            "rating_choices": Lead.CONVERSION_RATING_CHOICES,
        },
    )


@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    categories_selected = [c for c in request.GET.getlist("category") if c.strip()]
    statuses_selected = [s for s in request.GET.getlist("status") if s.strip()]
    states_selected = [s for s in request.GET.getlist("state") if s.strip()]
    cities_selected = [c for c in request.GET.getlist("city") if c.strip()]
    ratings_selected = [r for r in request.GET.getlist("rating") if r.strip()]
    filter_params = {
        key: request.GET[key]
        for key in ("q", "sort", "page", "has_email", "has_website", "has_phone")
        if request.GET.get(key)
    }
    filter_qs = urlencode(
        list(filter_params.items())
        + [("status", s) for s in statuses_selected]
        + [("state", s) for s in states_selected]
        + [("city", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
    )

    return_to = request.GET.get("return_to", "")
    if not return_to.startswith("/") or return_to.startswith("//"):
        return_to = ""

    if request.method == "POST":
        lead.delete()
        if return_to:
            return redirect(return_to)
        list_url = reverse("leads:list")
        if filter_qs:
            list_url += f"?{filter_qs}"
        return redirect(list_url)

    detail_qs = urlencode(
        list(filter_params.items())
        + [("status_filter", s) for s in statuses_selected]
        + [("state_filter", s) for s in states_selected]
        + [("city_filter", c) for c in cities_selected]
        + [("category", c) for c in categories_selected]
        + [("rating", r) for r in ratings_selected]
        + ([("return_to", return_to)] if return_to else [])
    )
    if return_to:
        filter_qs += ("&" if filter_qs else "") + urlencode([("return_to", return_to)])
    return render(
        request,
        "leads/lead_confirm_delete.html",
        {"lead": lead, "filter_qs": filter_qs, "detail_qs": detail_qs},
    )

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from payments.models import PaymentConfirmation
from core.models import Notification
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse
from django.http import HttpResponseRedirect
from properties.models import Property, PropertyImage, University, City


def admin_required(view_func):
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not (getattr(request.user, "role", None) == "admin" or request.user.is_staff or request.user.is_superuser):
            return redirect(f"/admin/login/?next={request.path}")
        return view_func(request, *args, **kwargs)

    return _wrapped


@admin_required
def payment_confirmations(request):
    # Handle AJAX approve/decline
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        action = request.POST.get("action")
        pk = request.POST.get("pk")
        confirmation = get_object_or_404(PaymentConfirmation, pk=pk)
        if action == "approve":
            confirmation.status = "approved"
            confirmation.save()
            confirmation.payment.activate()
            Notification.objects.create(recipient=confirmation.payment.user, title="Payment confirmed", message=f"Your payment for {confirmation.payment.university.name} has been approved.")
            return JsonResponse({"status": "approved", "pk": pk})
        elif action == "decline":
            confirmation.status = "declined"
            confirmation.save()
            Notification.objects.create(recipient=confirmation.payment.user, title="Payment declined", message=f"Your payment for {confirmation.payment.university.name} has been declined.")
            return JsonResponse({"status": "declined", "pk": pk})
        return JsonResponse({"error": "unknown action"}, status=400)

    # Regular page with pagination
    qs = PaymentConfirmation.objects.filter(status="pending").order_by("submitted_at")
    paginator = Paginator(qs, 10)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    return render(request, "web/payment_confirmations.html", {"page_obj": page_obj})


# Public site views

def home(request):
    from properties.models import Service
    
    services = []
    for service in Service.objects.filter(is_active=True):
        # Use image URL or fallback to static image
        if service.image:
            image_url = service.image.url
        else:
            image_url = f'/static/images/{service.slug}.jpg'
        
        services.append({
            'name': service.name,
            'url': f'/{service.slug}/' if service.property_type else '/',
            'bg': service.background_color,
            'image': image_url,
            'description': service.description,
        })
    
    return render(request, "web/home.html", {"services": services})


# --- Web Auth views (register, login, logout, profile)
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import WebRegisterForm, ProfileForm, PropertyForm, WebLoginForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = WebRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Account created. You can now log in.')
            return redirect('web-login')
    else:
        form = WebRegisterForm()
    return render(request, 'web/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = WebLoginForm(request.POST)
        if form.is_valid():
            identifier_user = form.cleaned_data.get("resolved_user")
            user = authenticate(request, email=identifier_user.email, password=form.cleaned_data["password"])
            if user is None:
                form.add_error(None, 'Invalid username/email or password.')
            else:
                auth_login(request, user)
                messages.success(request, 'Logged in successfully')
                next_url = request.GET.get('next') or '/'
                return redirect(next_url)
    else:
        form = WebLoginForm()
    return render(request, 'web/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.success(request, 'Logged out')
    return redirect('/')


@login_required
def profile_view(request):
    from payments.models import ContactView

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated')
            return redirect('web-profile')
    else:
        form = ProfileForm(instance=request.user)

    # Landlord dashboard info
    is_landlord = (getattr(request.user, 'role', None) == 'landlord') or request.user.is_staff or request.user.is_superuser
    landlord_properties = []
    landlord_activity = []
    if is_landlord:
        landlord_properties = Property.objects.filter(owner=request.user).prefetch_related('images').order_by('-created_at')
        landlord_activity = (
            ContactView.objects.filter(property__owner=request.user)
            .select_related('payment__user', 'property')
            .order_by('-viewed_at')[:50]
        )

    # Student/user booking history (closest concept: properties where user unlocked contact details)
    booking_history_qs = (
        ContactView.objects.filter(payment__user=request.user)
        .select_related('property')
        .order_by('-viewed_at')
    )
    seen_property_ids = set()
    booking_history = []
    for cv in booking_history_qs:
        if cv.property_id in seen_property_ids:
            continue
        seen_property_ids.add(cv.property_id)
        booking_history.append(cv)
        if len(booking_history) >= 50:
            break

    return render(
        request,
        'web/profile.html',
        {
            'form': form,
            'is_landlord': is_landlord,
            'landlord_properties': landlord_properties,
            'landlord_activity': landlord_activity,
            'booking_history': booking_history,
        },
    )


# Landlord web views
from django.contrib.auth.decorators import login_required


@login_required
def my_properties(request):
    props = Property.objects.filter(owner=request.user)
    return render(request, "web/my_properties.html", {"properties": props})


@login_required
def edit_property(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if getattr(request.user, "role", None) != "landlord" and not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            updated = form.save(commit=False)
            # Any edit should go back to pending approval
            updated.is_approved = False
            updated.save()

            # optional: append new uploaded images
            for f in request.FILES.getlist('images'):
                PropertyImage.objects.create(property=updated, image=f)

            # optional: delete selected images
            delete_ids = request.POST.getlist('delete_image')
            if delete_ids:
                PropertyImage.objects.filter(property=updated, id__in=delete_ids).delete()

            messages.success(request, 'Property updated (pending approval)')
            return redirect('dashboard-my-properties')
    else:
        form = PropertyForm(instance=prop)

    return render(request, 'web/edit_property.html', {'form': form, 'property': prop})


@login_required
def delete_property(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if getattr(request.user, "role", None) != "landlord" and not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)

    if request.method == 'POST':
        prop.delete()
        messages.success(request, 'Property deleted')
        return redirect('dashboard-my-properties')

    return render(request, 'web/delete_property.html', {'property': prop})


@login_required
def add_property(request):
    if getattr(request.user, "role", None) != "landlord" and not request.user.is_staff:
        return redirect('/admin/login/?next=/dashboard/properties/add/')

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.is_approved = False
            prop.save()

            # handle uploaded images
            for f in request.FILES.getlist('images'):
                PropertyImage.objects.create(property=prop, image=f)

            messages.success(request, "Property created and submitted for approval")
            return redirect('dashboard-my-properties')
    else:
        form = PropertyForm()

    return render(request, "web/add_property.html", {"form": form})


def universities(request):
    # list universities with admin fees
    from properties.models import University
    unis = University.objects.all().order_by('city__name', 'name')
    return render(request, "web/universities.html", {"unis": unis})


def university_properties(request, pk):
    from properties.models import Property, University
    q = request.GET.get("q")
    gender = request.GET.get("gender")
    sharing = request.GET.get("sharing")
    overnight = request.GET.get("overnight")

    qs = Property.objects.filter(is_approved=True, university_id=pk)
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
    if gender and gender != "all":
        qs = qs.filter(gender=gender)
    if sharing and sharing != "any":
        qs = qs.filter(sharing=sharing)
    if overnight == "1":
        qs = qs.filter(overnight=True)
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    try:
        if min_price:
            qs = qs.filter(nightly_price__gte=float(min_price))
        if max_price:
            qs = qs.filter(nightly_price__lte=float(max_price))
    except ValueError:
        pass

    # ordering and optional distance calculation
    order = request.GET.get("order")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius_km")
    properties = None
    if lat and lng:
        try:
            lat = float(lat)
            lng = float(lng)
            radius_val = float(radius) if radius else None
            results = []
            from math import radians, sin, cos, atan2, sqrt
            R = 6371
            for p in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
                try:
                    phi1 = radians(lat)
                    phi2 = radians(float(p.latitude))
                    dphi = radians(float(p.latitude) - lat)
                    dlambda = radians(float(p.longitude) - lng)
                    a = sin(dphi/2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda/2) ** 2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    distance = R * c
                    p.distance_km = round(distance, 2)
                    if radius_val is None or distance <= radius_val:
                        results.append(p)
                except Exception:
                    continue
            if order == "distance_desc":
                results.sort(key=lambda x: getattr(x, "distance_km", 9999), reverse=True)
            else:
                results.sort(key=lambda x: getattr(x, "distance_km", 9999))
            properties = results
        except ValueError:
            properties = qs
    else:
        if order in ("price_asc", "price_desc"):
            qs = qs.order_by("nightly_price" if order == "price_asc" else "-nightly_price")
        elif order == "newest":
            qs = qs.order_by("-created_at")
        properties = qs

    # paginate results (works for QuerySet or list)
    page_num = request.GET.get("page", 1)
    paginator = Paginator(list(properties), 10)
    page_obj = paginator.get_page(page_num)

    uni = University.objects.get(pk=pk)
    
    # Track university visit for notifications
    from core.models import UserUniversityPreference
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    if ip_address:
        pref, created = UserUniversityPreference.objects.get_or_create(
            ip_address=ip_address,
            university=uni,
            defaults={'user': request.user if request.user.is_authenticated else None}
        )
        if not created:
            pref.visit_count += 1
            if request.user.is_authenticated:
                pref.user = request.user
            pref.save()
    
    return render(request, "web/university_properties.html", {
        "page_obj": page_obj, 
        "university": uni,
        "uni": uni,  # Kept for backward compatibility
        "filters": {
            "gender": gender, 
            "sharing": sharing, 
            "overnight": overnight, 
            "min_price": min_price, 
            "max_price": max_price, 
            "order": order
        }
    })


import math

def _haversine(lat1, lon1, lat2, lon2):
    # returns distance in kilometers
    R = 6371  # Earth radius km
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def property_detail(request, pk):
    from properties.models import Property
    from payments.models import AdminFeePayment
    from django.db.models import Avg
    prop = get_object_or_404(Property, pk=pk)
    
    # Check if user has paid admin fee for this university
    has_paid = False
    if request.user.is_authenticated and prop.university:
        has_paid = AdminFeePayment.objects.filter(
            user=request.user,
            university=prop.university,
            uses_remaining__gt=0
        ).exists()
    
    # reviews
    all_reviews = prop.reviews.all().order_by("-created_at")
    recent_reviews = all_reviews[:5]  # Only latest 5
    total_reviews = all_reviews.count()
    average_rating = prop.reviews.aggregate(Avg('rating'))['rating__avg']
    distance_km = None
    if prop.university and prop.university.latitude and prop.university.longitude and prop.latitude and prop.longitude:
        try:
            distance_km = round(_haversine(prop.university.latitude, prop.university.longitude, prop.latitude, prop.longitude), 2)
        except Exception:
            distance_km = None

    user_review = None
    if request.user.is_authenticated:
        user_review = prop.reviews.filter(user=request.user).order_by("-created_at").first()

    return render(request, "web/property_detail.html", {
        "prop": prop, 
        "recent_reviews": recent_reviews,
        "all_reviews": all_reviews,
        "total_reviews": total_reviews,
        "average_rating": average_rating,
        "distance_km": distance_km,
        "has_paid": has_paid,
        "user_review": user_review,
    })


@login_required
def property_review_create(request, pk):
    from properties.models import Review

    if request.method != "POST":
        return redirect("web-property-detail", pk=pk)

    prop = get_object_or_404(Property, pk=pk)

    if Review.objects.filter(property=prop, user=request.user).exists():
        messages.info(request, "You already submitted a review for this accommodation. Remove it to submit a new one.")
        return redirect("web-property-detail", pk=pk)

    rating_raw = (request.POST.get("rating") or "").strip()
    comment = (request.POST.get("comment") or "").strip()

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        rating = None

    if rating not in (1, 2, 3, 4, 5):
        messages.error(request, "Please select a rating from 1 to 5.")
        return redirect("web-property-detail", pk=pk)

    if not comment:
        messages.error(request, "Please write a short review.")
        return redirect("web-property-detail", pk=pk)

    Review.objects.create(
        property=prop,
        user=request.user,
        rating=rating,
        comment=comment,
    )
    messages.success(request, "Thanks! Your review has been submitted.")

    return HttpResponseRedirect(reverse("web-property-detail", kwargs={"pk": pk}))


@login_required
def property_review_delete(request, pk):
    from properties.models import Review

    if request.method != "POST":
        return redirect("web-property-detail", pk=pk)

    prop = get_object_or_404(Property, pk=pk)
    qs = Review.objects.filter(property=prop, user=request.user)
    if not qs.exists():
        messages.info(request, "You don't have a review to remove.")
        return redirect("web-property-detail", pk=pk)

    qs.delete()
    messages.success(request, "Your review has been removed.")
    return redirect("web-property-detail", pk=pk)


@login_required
def property_contact(request, pk):
    from properties.models import Property
    from payments.models import AdminFeePayment, PaymentConfirmation, ContactView
    from core.models import Notification
    from django.contrib import messages
    
    prop = get_object_or_404(Property, pk=pk)
    
    # Check payment status for this university
    has_paid = False
    payment_status = None
    payment_confirmation = None
    active_payment = None
    already_viewed = False
    
    if request.user.is_authenticated and prop.university:
        # Check for approved payment with remaining uses
        active_payment = AdminFeePayment.objects.filter(
            user=request.user,
            university=prop.university,
            uses_remaining__gt=0
        ).first()
        
        if active_payment:
            # Check if user already viewed this property
            already_viewed = ContactView.objects.filter(
                payment=active_payment,
                property=prop
            ).exists()
            
            if not already_viewed:
                # First time viewing this property - decrement uses
                ContactView.objects.create(
                    payment=active_payment,
                    property=prop
                )
                active_payment.uses_remaining -= 1
                active_payment.save()
                
                # Notify user about remaining views
                if active_payment.uses_remaining > 0:
                    plural_suffix = "s" if active_payment.uses_remaining != 1 else ""
                    messages.success(
                        request, 
                        f"Contact details unlocked! You have {active_payment.uses_remaining} accommodation{plural_suffix} left to view."
                    )
                else:
                    messages.warning(
                        request,
                        "You have used all your accommodation viewing options. To view more properties, please pay the admin fee again."
                    )
            
            has_paid = True
        else:
            # Check for pending payment confirmation
            # Get the most recent payment confirmation for this university
            recent_payments = AdminFeePayment.objects.filter(
                user=request.user,
                university=prop.university
            ).order_by('-created_at')
            
            for payment in recent_payments:
                confirmation = payment.confirmations.order_by('-submitted_at').first()
                if confirmation:
                    payment_confirmation = confirmation
                    payment_status = confirmation.status
                    break
    
    return render(request, "web/property_contact.html", {
        "prop": prop,
        "has_paid": has_paid,
        "payment_status": payment_status,
        "payment_confirmation": payment_confirmation,
        "uses_remaining": active_payment.uses_remaining if active_payment else 0,
        "already_viewed": already_viewed,
    })


def realestate_cities(request):
    """List cities with real estate properties (resorts, lodges, shops)"""
    from django.db.models import Count, Q

    filter_type = request.GET.get('type')
    if filter_type == 'lodge':
        filter_type = 'real_estate'

    allowed_types = ['real_estate', 'resort', 'shop']
    types = allowed_types if not filter_type or filter_type == 'all' else [filter_type]
    
    # Get cities that have real estate properties
    cities = City.objects.filter(
        property__is_approved=True,
        property__property_type__in=types
    ).annotate(
        property_count=Count('property', filter=Q(property__is_approved=True, property__property_type__in=types))
    ).filter(property_count__gt=0).distinct()
    
    cities_data = []
    for city in cities:
        props = Property.objects.filter(
            city=city,
            is_approved=True,
            property_type__in=types
        )

        first_prop = props.first()
        sample_image = None
        if first_prop and first_prop.images.exists():
            sample_image = first_prop.images.first().image.url
        
        city_info = {
            'city': city,
            'count': props.count(),
            'resorts_count': props.filter(property_type='resort').count(),
            'lodges_count': props.filter(property_type='real_estate').count(),
            'shops_count': props.filter(property_type='shop').count(),
            'has_resorts': props.filter(property_type='resort').exists(),
            'has_lodges': props.filter(property_type='real_estate').exists(),
            'has_shops': props.filter(property_type='shop').exists(),
            'sample_image': sample_image,
        }
        cities_data.append(city_info)
    
    return render(request, "web/realestate_cities.html", {"cities": cities_data, "filter_type": filter_type or "all"})


def realestate_properties(request):
    """List real estate properties with filters"""
    city_id = request.GET.get('city')
    property_subtype = request.GET.get('subtype')

    if property_subtype == 'lodge':
        property_subtype = 'real_estate'
    
    qs = Property.objects.filter(is_approved=True, property_type__in=['real_estate', 'resort', 'shop'])
    
    city = None
    if city_id:
        city = get_object_or_404(City, pk=city_id)
        qs = qs.filter(city=city)
    
    if property_subtype:
        qs = qs.filter(property_type=property_subtype)
    
    # Order by newest first
    qs = qs.order_by('-created_at')
    
    return render(request, "web/realestate_properties.html", {
        "properties": qs,
        "city": city,
        "property_subtype": property_subtype
    })


def resort_cities(request):
    """List cities with resort properties"""
    from django.db.models import Count, Q
    
    cities = City.objects.filter(
        property__is_approved=True,
        property__property_type='resort'
    ).annotate(
        property_count=Count('property', filter=Q(property__is_approved=True, property__property_type='resort'))
    ).filter(property_count__gt=0).distinct()
    
    cities_data = []
    for city in cities:
        props = Property.objects.filter(
            city=city,
            is_approved=True,
            property_type='resort'
        )
        
        city_info = {
            'city': city,
            'count': props.count(),
            'sample_image': props.first().images.first().image.url if props.exists() and props.first().images.exists() else None
        }
        cities_data.append(city_info)
    
    return render(request, "web/resort_cities.html", {"cities": cities_data})


def resort_properties(request):
    """List resort properties with filters"""
    city_id = request.GET.get('city')
    
    qs = Property.objects.filter(is_approved=True, property_type='resort')
    
    city = None
    if city_id:
        city = get_object_or_404(City, pk=city_id)
        qs = qs.filter(city=city)
    
    qs = qs.order_by('-created_at')
    
    return render(request, "web/resort_properties.html", {
        "properties": qs,
        "city": city
    })


def shop_cities(request):
    """List cities with shop properties"""
    cities = City.objects.all().order_by('name')

    cities_data = []
    for city in cities:
        props = Property.objects.filter(city=city, is_approved=True, property_type='shop')

        first_prop = props.first()
        sample_image = None
        if first_prop and first_prop.images.exists():
            sample_image = first_prop.images.first().image.url

        cities_data.append({
            'city': city,
            'count': props.count(),
            'sample_image': sample_image,
        })

    return render(request, "web/shop_cities.html", {"cities": cities_data})


def shop_properties(request):
    """List shop properties with filters"""
    city_id = request.GET.get('city')

    qs = Property.objects.filter(is_approved=True, property_type='shop')

    city = None
    if city_id:
        city = get_object_or_404(City, pk=city_id)
        qs = qs.filter(city=city)

    qs = qs.order_by('-created_at')

    return render(request, "web/shop_properties.html", {
        "properties": qs,
        "city": city
    })


def longterm_cities(request):
    """List cities with long-term accommodation properties"""
    cities = City.objects.all().order_by('name')
    
    cities_data = []
    for city in cities:
        props = Property.objects.filter(
            city=city,
            is_approved=True,
            property_type='long_term'
        )

        first_prop = props.first()
        sample_image = None
        if first_prop and first_prop.images.exists():
            sample_image = first_prop.images.first().image.url
        
        city_info = {
            'city': city,
            'count': props.count(),
            'sample_image': sample_image,
            'min_price': props.aggregate(min_price=models.Min('price_per_month'))['min_price'],
            'max_price': props.aggregate(max_price=models.Max('price_per_month'))['max_price'],
        }
        cities_data.append(city_info)
    
    return render(request, "web/longterm_cities.html", {"cities": cities_data})


def longterm_properties(request):
    """List long-term properties with filters"""
    city_id = request.GET.get('city')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    qs = Property.objects.filter(is_approved=True, property_type='long_term')
    
    city = None
    if city_id:
        city = get_object_or_404(City, pk=city_id)
        qs = qs.filter(city=city)
    
    if min_price:
        try:
            qs = qs.filter(price_per_month__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            qs = qs.filter(price_per_month__lte=float(max_price))
        except ValueError:
            pass
    
    qs = qs.order_by('-created_at')
    
    return render(request, "web/longterm_properties.html", {
        "properties": qs,
        "city": city,
        "min_price": min_price,
        "max_price": max_price
    })


def shortterm_cities(request):
    """List cities with short-term accommodation properties"""
    from django.db.models import Count, Q
    
    cities = City.objects.filter(
        property__is_approved=True,
        property__property_type='short_term'
    ).annotate(
        property_count=Count('property', filter=Q(property__is_approved=True, property__property_type='short_term'))
    ).filter(property_count__gt=0).distinct()
    
    cities_data = []
    for city in cities:
        props = Property.objects.filter(
            city=city,
            is_approved=True,
            property_type='short_term'
        )

        first_prop = props.first()
        sample_image = None
        if first_prop and first_prop.images.exists():
            sample_image = first_prop.images.first().image.url
        
        city_info = {
            'city': city,
            'count': props.count(),
            'sample_image': sample_image,
            'min_price': props.aggregate(min_price=models.Min('nightly_price'))['min_price'],
            'max_price': props.aggregate(max_price=models.Max('nightly_price'))['max_price'],
        }
        cities_data.append(city_info)
    
    return render(request, "web/shortterm_cities.html", {"cities": cities_data})


def shortterm_properties(request):
    """List short-term properties with filters"""
    city_id = request.GET.get('city')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    guests = request.GET.get('guests')
    
    qs = Property.objects.filter(is_approved=True, property_type='short_term')
    
    city = None
    if city_id:
        city = get_object_or_404(City, pk=city_id)
        qs = qs.filter(city=city)
    
    if min_price:
        try:
            qs = qs.filter(nightly_price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            qs = qs.filter(nightly_price__lte=float(max_price))
        except ValueError:
            pass
    
    if guests:
        try:
            qs = qs.filter(max_occupancy__gte=int(guests))
        except ValueError:
            pass
    
    qs = qs.order_by('-created_at')
    
    return render(request, "web/shortterm_properties.html", {
        "properties": qs,
        "city": city,
        "min_price": min_price,
        "max_price": max_price,
        "guests": guests
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully')
            return redirect('web-profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'web/change_password.html', {'form': form})


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='web/password_reset_email.txt',
                subject_template_name='web/password_reset_subject.txt'
            )
            messages.success(request, 'Password reset email sent')
            return redirect('web-login')
    else:
        form = PasswordResetForm()
    return render(request, 'web/password_reset.html', {'form': form})


@login_required
def toggle_property_like(request, property_id):
    """Toggle like status for a property"""
    try:
        property_obj = Property.objects.get(id=property_id)
        # For now, just return success. In future, implement actual like system
        return JsonResponse({'liked': True})
    except Property.DoesNotExist:
        return JsonResponse({'error': 'Property not found'}, status=404)


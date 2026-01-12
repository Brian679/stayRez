from django import forms
from accounts.models import User
from properties.models import Property


class WebLoginForm(forms.Form):
    identifier = forms.CharField(label="Username or email", max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        identifier = (cleaned.get("identifier") or "").strip()
        password = cleaned.get("password")

        if not identifier or not password:
            return cleaned

        # Resolve to a user by username or email.
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user:
            raise forms.ValidationError("Invalid username/email or password.")

        cleaned["resolved_user"] = user
        return cleaned


class WebRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['full_name'].required = True

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email', 'phone_number', 'address', 'role', 'password')


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    role = forms.CharField(disabled=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'full_name', 'phone_number', 'address', 'email', 'role')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('Email is required.')
        return email


class PropertyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure user selects listing type first.
        if "property_type" in self.fields:
            choices = list(self.fields["property_type"].choices)
            if choices and choices[0][0] != "":
                self.fields["property_type"].choices = [("", "Select listing type...")] + choices

        # Better UX: placeholders for text/number inputs.
        placeholders = {
            "title": "e.g., Modern 2-bedroom apartment" ,
            "description": "Describe the property (rooms, rules, what’s included, nearby places)...",
            "location": "Street / area (e.g., Westlands, near ABC Mall)",
            "latitude": "e.g., -1.292065",
            "longitude": "e.g., 36.821946",
            "contact_phone": "e.g., +254 700 000 000",
            "house_number": "House/plot number (if applicable)",
            "caretaker_number": "Caretaker/agent phone (optional)",
            "nightly_price": "e.g., 3500",
            "price_per_month": "e.g., 18000",
            "amenities": "e.g., WiFi, Parking, Kitchen, Security",
            "max_occupancy": "e.g., 4",
            "distance_to_campus_km": "e.g., 1.5",
            "square_meters": "e.g., 85",
            "bedrooms": "e.g., 2",
            "bathrooms": "e.g., 1",
            "rating_stars": "1 to 5",
            "shop_category": "e.g., Grocery, Salon, Electronics",
        }

        for name, field in self.fields.items():
            widget = field.widget

            # Add bootstrap-friendly classes where applicable.
            if isinstance(widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, forms.URLInput, forms.Textarea, forms.Select)):
                widget.attrs.setdefault("class", "form-control")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")

            if name in placeholders and isinstance(widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                widget.attrs.setdefault("placeholder", placeholders[name])

        # More descriptive dropdown placeholders
        if "university" in self.fields and hasattr(self.fields["university"], "empty_label"):
            self.fields["university"].empty_label = "Select university (students only)"
        if "city" in self.fields and hasattr(self.fields["city"], "empty_label"):
            self.fields["city"].empty_label = "Select city"

    def clean(self):
        cleaned = super().clean()
        ptype = cleaned.get("property_type")

        # If listing type isn't chosen yet, stop early.
        if not ptype:
            return cleaned

        # Prevent stale/irrelevant data sticking around when users switch types.
        student_only = {"university", "gender", "sharing", "overnight", "nightly_price", "price_per_month", "max_occupancy", "distance_to_campus_km", "caretaker_number"}
        real_estate_only = {"square_meters", "bedrooms", "bathrooms"}
        resort_only = {"rating_stars", "all_inclusive"}
        shop_only = {"shop_category"}

        keep = set()
        if ptype == "students":
            keep |= student_only
        elif ptype == "real_estate":
            keep |= real_estate_only
        elif ptype == "resort":
            keep |= resort_only
        elif ptype == "shop":
            keep |= shop_only
        elif ptype == "short_term":
            # short-term stays: nightly price + capacity are the key extras
            keep |= {"nightly_price", "max_occupancy", "rating_stars", "all_inclusive"}
        elif ptype == "long_term":
            # long-term stays: monthly price is the key extra
            keep |= {"price_per_month", "max_occupancy"}

        all_specific = student_only | real_estate_only | resort_only | shop_only
        for fname in all_specific:
            if fname in cleaned and fname not in keep:
                if isinstance(self.fields.get(fname), forms.BooleanField):
                    cleaned[fname] = False
                else:
                    cleaned[fname] = None if fname != "shop_category" else ""

        return cleaned

    class Meta:
        model = Property
        fields = (
            'title',
            'description',
            'property_type',
            'university',
            'city',
            'is_available',
            'location',
            'latitude',
            'longitude',
            'contact_phone',
            'house_number',
            'caretaker_number',
            'gender',
            'overnight',
            'sharing',
            'nightly_price',
            'price_per_month',
            'amenities',
            'max_occupancy',
            'distance_to_campus_km',
            'square_meters',
            'bedrooms',
            'bathrooms',
            'rating_stars',
            'all_inclusive',
            'shop_category',
        )


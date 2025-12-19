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
    class Meta:
        model = Property
        fields = (
            'title',
            'description',
            'property_type',
            'university',
            'city',
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


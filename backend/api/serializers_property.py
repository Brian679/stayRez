from rest_framework import serializers
from properties.models import Property, PropertyImage


class PropertyCreateSerializer(serializers.ModelSerializer):
    # Use FileField to be tolerant in tests and dev envs; in production consider ImageField with Pillow installed.
    images = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
    existing_images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "title",
            "description",
            "property_type",
            "university",
            "city",
            "location",
            "latitude",
            "longitude",
            "contact_phone",
            "house_number",
            "caretaker_number",
            "gender",
            "overnight",
            "sharing",
            "nightly_price",
            "price_per_month",
            "amenities",
            "max_occupancy",
            "distance_to_campus_km",
            "square_meters",
            "bedrooms",
            "bathrooms",
            "rating_stars",
            "all_inclusive",
            "shop_category",
            "existing_images",
            "images",
        )

    def get_existing_images(self, obj):
        request = self.context.get("request")
        out = []
        for img in obj.images.all():
            try:
                url = img.image.url
                if request:
                    url = request.build_absolute_uri(url)
            except Exception:
                url = None
            out.append({"id": img.id, "image": url})
        return out

    def create(self, validated_data):
        # accept images passed in validated_data as a list or as files in request.FILES
        images = validated_data.pop("images", None)
        request = self.context.get("request")
        if not images and request is not None:
            # DRF's request.FILES may have 'images' as a list or single file
            try:
                files = request.FILES.getlist("images")
                if files:
                    images = files
            except Exception:
                # single file fallback
                single = request.FILES.get("images")
                if single:
                    images = [single]
            # also handle other multipart naming like images[0], images[]
            if not images:
                collected = []
                for key, val in request.FILES.items():
                    if key.startswith("images"):
                        # val may be UploadedFile or list-like
                        try:
                            for f in val:
                                collected.append(f)
                        except Exception:
                            collected.append(val)
                if collected:
                    images = collected
        if images is None:
            images = []
        user = request.user if request is not None else None
        prop = Property.objects.create(owner=user, **validated_data)
        for img in images:
            PropertyImage.objects.create(property=prop, image=img)
        return prop

    def update(self, instance, validated_data):
        # Support updating basic fields + optionally adding/removing images.
        images = validated_data.pop("images", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        request = self.context.get("request")

        # Optional delete by ids: delete_image_ids=[1,2] (JSON) or "1,2" (form)
        delete_ids = []
        if request is not None:
            raw = request.data.get("delete_image_ids")
            if raw:
                if isinstance(raw, (list, tuple)):
                    delete_ids = list(raw)
                elif isinstance(raw, str):
                    delete_ids = [s.strip() for s in raw.split(",") if s.strip()]
                else:
                    delete_ids = [raw]
        # Coerce to ints
        coerced_ids = []
        for val in delete_ids:
            try:
                coerced_ids.append(int(val))
            except Exception:
                continue
        if coerced_ids:
            PropertyImage.objects.filter(property=instance, id__in=coerced_ids).delete()

        # Add any newly uploaded images
        if request is not None:
            # Prefer validated_data-provided list, else gather from request.FILES
            if not images:
                try:
                    files = request.FILES.getlist("images")
                    if files:
                        images = files
                except Exception:
                    single = request.FILES.get("images")
                    if single:
                        images = [single]
            if not images:
                collected = []
                for key, val in request.FILES.items():
                    if key.startswith("images"):
                        try:
                            for f in val:
                                collected.append(f)
                        except Exception:
                            collected.append(val)
                if collected:
                    images = collected

        if images:
            for img in images:
                PropertyImage.objects.create(property=instance, image=img)

        return instance


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ("id", "image")

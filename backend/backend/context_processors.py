from properties.models import University


def universities(request):
    """Make universities available to all templates"""
    return {
        'universities': University.objects.all().order_by('name')
    }

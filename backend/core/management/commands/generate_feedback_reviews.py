from django.core.management.base import BaseCommand
from core.models_feedback import Feedback
import random

NAMES = [
    # English/neutral names
    "Alex", "Sam", "Chris", "Pat", "Jordan", "Taylor", "Morgan", "Casey", "Jamie", "Robin",
    "Drew", "Skyler", "Avery", "Riley", "Cameron", "Quinn", "Jesse", "Harper", "Reese", "Rowan",
    # Shona names
    "Tendai", "Tatenda", "Ruvimbo", "Tafadzwa", "Kudakwashe", "Rumbidzai", "Tawanda", "Nyasha", "Farai", "Chipo",
    "Simba", "Munyaradzi", "Rutendo", "Shingirai", "Vimbai", "Takudzwa", "Chenai", "Kudzai", "Anesu", "Rudo",
    "Tsitsi", "Munashe", "Tariro", "Fadzai", "Tanaka", "Makanaka", "Tanyaradzwa", "Tinashe", "Tendekai", "Blessing"
]
CITIES = ["Harare", "Chinhoyi", "Gweru", "Bindura", "Masvingo"]
OCCUPATIONS = ["Student", "Tenant", "Landlord", "Real Estate Agent"]
AGES = ["Below 18", "18–25", "26–35", "36–45", "Above 45"]
GENDERS = ["Male", "Female", "Prefer not to say"]

LIKES = [
    "Easy to use", "Good map features", "Accurate info", "Nice design", "Quick search", "Responsive UI",
    "Helpful filters", "Mobile friendly", "Clear property details", "Trustworthy"
]
CHALLENGES = [
    "Limited options", "Occasional slow loading", "Some listings outdated", "Map could be clearer",
    "More photos needed", "Minor bugs"
]
IMPROVEMENTS = [
    "Add more properties", "Improve map", "Faster loading", "More filters", "Better mobile support",
    "Add reviews for landlords"
]

RATING_POOL = [3, 4, 4, 4, 4, 5, 5]  # Weighted for average ~4

class Command(BaseCommand):
    help = "Generate 200 random feedback reviews with average rating ~4."

    def handle(self, *args, **options):
        feedbacks = []
        for i in range(200):
            rating = random.choice(RATING_POOL)
            feedbacks.append(Feedback(
                satisfaction=rating,
                ease_of_use=rating,
                recommend=rating,
                like_most=random.choice(LIKES),
                improvements=random.choice(IMPROVEMENTS),
            ))
        Feedback.objects.bulk_create(feedbacks)
        self.stdout.write(self.style.SUCCESS('Successfully added 200 feedback reviews.'))

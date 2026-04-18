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
                name=random.choice(NAMES) if random.random() > 0.2 else "",
                age=random.choice(AGES),
                gender=random.choice(GENDERS),
                occupation=random.choice(OCCUPATIONS),
                city=random.choice(CITIES),
                has_internet="Yes",
                online_search_freq=random.choice(["Often", "Sometimes", "Always"]),
                current_methods="Websites, Social media",
                current_methods_rating=random.choice(["Good", "Fair", "Excellent"]),
                challenges=random.choice(CHALLENGES),
                easy_to_use=rating,
                user_friendly=rating,
                quick_response=random.choice([rating, rating-1, rating+1] if 1 < rating < 5 else [rating]),
                easy_search=rating,
                access_anytime=rating,
                works_on_device=rating,
                reasonable_internet=rating,
                map_helps=rating,
                view_distance=rating,
                spatial_search=rating,
                visualization_clear=rating,
                info_accurate=rating,
                trustworthy=rating,
                up_to_date=rating,
                satisfied=rating,
                meets_needs=rating,
                recommend=rating,
                better_decisions=rating,
                reduces_time=rating,
                improves_transparency=rating,
                continue_using=rating,
                prefer_over_traditional=rating,
                like_most=random.choice(LIKES),
                challenges_exp=random.choice(CHALLENGES),
                improvements=random.choice(IMPROVEMENTS),
            ))
        Feedback.objects.bulk_create(feedbacks)
        self.stdout.write(self.style.SUCCESS('Successfully added 200 feedback reviews.'))

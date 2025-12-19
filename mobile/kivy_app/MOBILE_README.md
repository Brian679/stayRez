# offRez Mobile App

A Kivy-based mobile application for the offRez student accommodation platform.

## Features

The mobile app now has full feature parity with the web application, including:

### Core Functionality
- **Home Screen**: Dynamic service tiles loaded from API
- **University Listings**: Browse all universities with admin fees
- **Property Listings**: View properties for each university with filters
- **Property Details**: Detailed property view with images, reviews, and contact options

### User Features
- **Authentication**: Login and registration
- **Profile Management**: View and edit user profile
- **Session Persistence**: Maintains login state across app usage
- **Notifications**: Real-time notifications for payments and property updates

### Property Features
- **Advanced Filtering**: Filter by gender, sharing type, overnight guests, price range, and sorting
- **Reviews & Ratings**: View property reviews and average ratings
- **Distance Calculation**: Shows distance from university
- **Image Gallery**: Property photos display

### Payment & Contact
- **Admin Fee Payment**: Calculate and submit admin fee payments
- **Payment Confirmation**: Submit payment confirmation for admin approval
- **Contact Landlord**: View landlord contact details after payment approval
- **Payment Status Tracking**: Track pending/approved/declined payment status

### Landlord Features
- **My Properties**: View all properties owned by landlord
- **Property Status**: See approval status for each property
- **Property Management**: Quick access to property details

## Screens

1. **HomeScreen** - Service tiles with dynamic navigation
2. **UniversitiesScreen** - List of all universities
3. **PropertyListScreen** - Filtered property listings
4. **PropertyDetailScreen** - Detailed property view with reviews
5. **PropertyContactScreen** - Payment and contact management
6. **LoginScreen** - User authentication
7. **RegisterScreen** - New user registration
8. **ProfileScreen** - User profile management
9. **NotificationsScreen** - Notification center
10. **MyPropertiesScreen** - Landlord property management

## Technical Architecture

### Session Management
- `SessionManager` class handles user authentication state
- Persists user data across screens
- Manages login/logout lifecycle

### API Integration
All screens communicate with the Django REST API:
- `GET /api/services/` - Load service tiles
- `GET /api/universities/` - List universities
- `GET /api/universities/{id}/properties/` - List properties with filters
- `GET /api/properties/{id}/` - Property details
- `POST /api/properties/{id}/contact/` - Contact landlord
- `POST /api/login/` - User login
- `POST /api/register/` - User registration
- `GET /api/profile/` - Get user profile
- `PATCH /api/profile/` - Update user profile
- `GET /api/notifications/` - Get notifications
- `GET /api/landlord/properties/` - Get landlord properties
- `POST /api/payments/confirm/` - Submit payment confirmation

### Property Filters
PropertyListScreen supports URL parameters:
- `gender` - Filter by gender preference (male/female/all)
- `sharing` - Filter by room sharing (single/double/any)
- `overnight` - Filter for overnight guest policies
- `min_price` - Minimum nightly price
- `max_price` - Maximum nightly price
- `order` - Sort order (price_asc, price_desc, newest, distance)

### UI/UX Features
- Responsive design adapts to screen size
- Fade-in animations for smooth loading
- Pulse animations for loading states
- Color-coded status indicators
- Touch-friendly button sizes
- Scrollable content containers

## Installation

1. Install Python 3.8+
2. Install dependencies:
```bash
pip install kivy
```

3. Run the app:
```bash
cd mobile/kivy_app
python main.py
```

## Configuration

### API Endpoint
Update `API_BASE` in `main.py` to point to your backend:
```python
API_BASE = "http://127.0.0.1:8000/api/"  # Development
# API_BASE = "https://your-domain.com/api/"  # Production
```

### Assets
Place service images in the `assets/` directory:
- `students.png` - Students accommodation
- `longterm.png` - Long-term rentals
- `shortterm.png` - Short-term stays
- `realestate.png` - Real estate

## File Structure

```
mobile/kivy_app/
├── main.py              # Main application logic
├── offrez.kv           # UI definitions for main screens
├── screens_extra.kv    # UI definitions for extra screens
├── assets/             # Image assets
└── README.md           # This file
```

## Development

### Adding New Screens
1. Create screen class in `main.py`:
```python
class MyNewScreen(Screen):
    def on_pre_enter(self):
        # Load data when entering screen
        pass
```

2. Add screen to ScreenManager:
```python
sm.add_widget(MyNewScreen(name='my_new_screen'))
```

3. Define UI in KV file:
```kv
<MyNewScreen>:
    BoxLayout:
        orientation: 'vertical'
        # UI elements here
```

### Using SessionManager
```python
# Get session instance
session = SessionManager()

# Check if logged in
if session.is_logged_in():
    user = session.get_user()
    
# Store user data after login
session.set_user(user_data)

# Clear on logout
session.clear_user()
```

### Making API Requests
```python
from kivy.network.urlrequest import UrlRequest
import json

# GET request
UrlRequest(
    API_BASE + 'endpoint/',
    on_success=self.on_success,
    on_error=self.on_error
)

# POST request with JSON
headers = {'Content-Type': 'application/json'}
data = json.dumps({'key': 'value'})
UrlRequest(
    API_BASE + 'endpoint/',
    on_success=self.on_success,
    on_error=self.on_error,
    req_body=data,
    req_headers=headers,
    method='POST'
)
```

## Known Limitations

1. **Cookie-based Sessions**: The app uses session cookies for authentication. Ensure the backend has proper CORS and session settings.
2. **Image Caching**: AsyncImage may cache images. Clear cache if property images don't update.
3. **Network Errors**: Limited offline support - requires active connection.

## Future Enhancements

- [ ] Add property creation form for landlords
- [ ] Implement image upload for properties
- [ ] Add review submission functionality
- [ ] Implement real-time chat with landlords
- [ ] Add push notifications
- [ ] Offline caching of property listings
- [ ] Map view integration
- [ ] Save favorite properties
- [ ] Payment integration (mobile money)

## Testing

Test the app with a running backend:
1. Start Django backend: `python manage.py runserver`
2. Run mobile app: `python main.py`
3. Test each screen flow:
   - Register new account
   - Login
   - Browse universities
   - View properties
   - Submit payment confirmation
   - View notifications
   - Update profile

## Troubleshooting

### KV File Not Loading
Check `offrez_kv_error.log` for detailed error messages.

### API Connection Failed
- Verify backend is running
- Check `API_BASE` URL is correct
- Ensure CORS is configured in Django settings

### Screen Not Displaying
- Check screen is added to ScreenManager
- Verify screen name matches navigation code
- Check KV file syntax

### Images Not Loading
- Verify image paths in `assets/` directory
- Check AsyncImage source URLs
- Ensure images are accessible from backend

## License

Part of the offRez platform project.

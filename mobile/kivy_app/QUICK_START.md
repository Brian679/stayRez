# Quick Start Guide - offRez Mobile App

## Running the App

### 1. Start the Backend
```bash
cd backend
python manage.py runserver
```
Backend will run at: `http://127.0.0.1:8000`

### 2. Run the Mobile App
```bash
cd mobile/kivy_app
python main.py
```

## Test User Flows

### New User Journey
1. **Open App** → Home screen with service tiles
2. **Click Register** → Fill form (email, password, first/last name)
3. **Submit Registration** → Auto-redirect to Login
4. **Login** → Enter credentials
5. **Home Screen** → Now logged in, can see profile/notification buttons

### Browse Properties
1. **Click "Students Accommodation"** → Universities list
2. **Select University** → Properties list for that university
3. **Try Filters**:
   - Gender: All/Male/Female
   - Sharing: Single/Double/Any
   - Price range: Min/Max
   - Sort: Price, Newest, Distance
4. **Click Property** → Property details with reviews

### Payment Flow
1. **On Property Detail** → Click "Contact Landlord"
2. **PropertyContact Screen** → See payment form
3. **Enter Number of Students** → e.g., "2"
4. **Calculate Admin Fee** → Shows total amount
5. **Payment Instructions** → Ecocash number displayed
6. **Paste Confirmation** → Submit payment confirmation
7. **Success Message** → "Payment submitted, pending approval"

### Profile Management
1. **Click Profile Icon (👤)** → Profile screen
2. **Edit Name** → Change first/last name
3. **Click Save** → Updates saved
4. **Back to Home** → Changes persist

### Notifications
1. **Click Notification Icon (🔔)** → Notifications screen
2. **See All Notifications** → Payment updates, property alerts
3. **Read Status** → Unread shown in blue background

### Landlord Features
1. **Login as Landlord** → Use landlord account
2. **Navigate to My Properties** → View owned properties
3. **See Status** → Approved/Pending properties
4. **Click Property** → View details

## Testing Checklist

### Authentication
- [ ] Register creates new account
- [ ] Login succeeds with correct credentials
- [ ] Login fails with wrong credentials
- [ ] Session persists across screens
- [ ] Profile loads user data

### Property Browsing
- [ ] Services load from API on home screen
- [ ] Universities list loads
- [ ] Properties load for selected university
- [ ] Filters apply correctly:
  - [ ] Gender filter
  - [ ] Sharing filter
  - [ ] Price range filter
  - [ ] Sort order
- [ ] Property images display
- [ ] Property details load
- [ ] Reviews display

### Payment System
- [ ] Contact screen loads
- [ ] Admin fee calculation works
- [ ] Payment instructions display
- [ ] Payment confirmation submits
- [ ] Contact details show after approval (test with admin approval)

### UI/UX
- [ ] Animations smooth (fade-in, pulse)
- [ ] Loading states show
- [ ] Error messages display
- [ ] Back buttons work
- [ ] Navigation flows correctly
- [ ] Responsive on different screen sizes

### Edge Cases
- [ ] Empty property lists
- [ ] No notifications
- [ ] No landlord properties
- [ ] Network failure handling
- [ ] Invalid input handling

## Common Issues & Solutions

### App Won't Start
**Problem**: Import errors or missing dependencies
**Solution**: 
```bash
pip install kivy
```

### KV File Not Loading
**Problem**: KV syntax error
**Solution**: Check `offrez_kv_error.log` for details

### API Connection Failed
**Problem**: Backend not running or wrong URL
**Solution**: 
1. Verify backend is running: `http://127.0.0.1:8000`
2. Check `API_BASE` in main.py

### Images Not Displaying
**Problem**: Missing asset files
**Solution**: Ensure images exist in `assets/` directory:
- students.png
- longterm.png
- shortterm.png
- realestate.png

### Session Not Persisting
**Problem**: SessionManager not working
**Solution**: Check login success handler stores user data

### Blank Screens
**Problem**: Screen not found or KV error
**Solution**: 
1. Verify screen added to ScreenManager
2. Check screen name matches navigation
3. Validate KV syntax

## API Endpoints Reference

```python
# Base URL
API_BASE = "http://127.0.0.1:8000/api/"

# Services
GET /api/services/

# Universities
GET /api/universities/
GET /api/universities/{id}/

# Properties
GET /api/universities/{id}/properties/
GET /api/properties/{id}/

# Auth
POST /api/login/
POST /api/register/
POST /api/logout/

# Profile
GET /api/profile/
PATCH /api/profile/

# Notifications
GET /api/notifications/

# Landlord
GET /api/landlord/properties/

# Payments
POST /api/properties/{id}/contact/
POST /api/payments/confirm/
```

## Quick Feature Access

### Screen Navigation Map
```
Home (home)
├── Login (login)
├── Register (register)
├── Profile (profile)
├── Notifications (notifications)
├── Universities (universities)
│   └── Properties (properties)
│       └── Property Detail (property_detail)
│           └── Contact (property_contact)
└── My Properties (my_properties) [Landlord only]
```

### Button/Icon Guide
- 🔔 → Notifications
- 👤 → Profile
- ← Back → Previous screen
- Login → Authentication
- Register → New account
- Contact Landlord → Payment/Contact flow

## Performance Tips

1. **First Load**: May be slow as images download
2. **Subsequent Loads**: Faster due to image caching
3. **Filters**: Apply filters sequentially (one at a time) for best experience
4. **Scrolling**: Large property lists may lag initially

## Development Mode

### Enable Debug Output
Already enabled - check terminal for:
- API request URLs
- Response data
- Screen transitions
- Error messages

### Test Different Users
Create test accounts:
1. General user (for property browsing)
2. Landlord (for property management)
3. Admin (for backend approval)

### Modify for Testing
```python
# In main.py, change API_BASE for different environments
API_BASE = "http://127.0.0.1:8000/api/"  # Local
API_BASE = "http://192.168.1.x:8000/api/"  # LAN testing
API_BASE = "https://your-domain.com/api/"  # Production
```

## Next Steps

1. **Test All Flows** → Go through each checklist item
2. **Report Issues** → Document any bugs found
3. **Build APK** → Use buildozer for Android deployment
4. **Deploy Backend** → Host Django on production server
5. **Update API_BASE** → Point to production URL
6. **Submit to Store** → Google Play/App Store

## Support

For issues or questions:
1. Check this guide
2. Review BUILD_SUMMARY.md
3. Read MOBILE_README.md
4. Check backend README.md
5. Review API documentation

---

**Ready to Test!** Start with the backend running, then launch the mobile app and follow the test flows above.

# Long-term Accommodation Flow Implementation

## Overview
Complete implementation of the long-term accommodation navigation flow, matching the design patterns used for student accommodations.

## Navigation Flow

### 1. Home Screen → LocationListScreen
- **Trigger**: Click on "Long-term accommodation" tile on HomeScreen
- **Handler**: `HomeScreen.navigate_to_longterm()`
- **Screen**: `LocationListScreen`

### 2. LocationListScreen
**Purpose**: Display available cities with long-term properties

**Design**: Simple and clean - just city names in bordered cards

**Features**:
- Fetches all long-term properties from API
- Extracts unique cities from property data
- Displays cities in simple, clean cards with:
  - City name (bold, centered-left)
  - White background with light gray border
  - Border radius for smooth corners
  - Arrow indicator (→) on the right
  - Responsive grid (1 column <600dp, 2 columns ≥600dp)
  - **Off-Rez header** (back, logo, notifications, menu)

**API Endpoint**: `GET /api/properties/?property_type=longterm`

**Card Design**:
```python
- White card with light gray border (#E0E0E0)
- City name: sp(16-18), bold, dark gray
- Card height: 70dp (small) / 80dp (large)
- Border radius: 12dp
- Horizontal layout with arrow on right
- Responsive spacing and padding
```

### 3. LocationListScreen → PropertyListScreen
**Trigger**: Click on city card

**Handler**: 
```python
def on_click(_):
    props_screen = self.manager.get_screen('properties')
    props_screen.load_for_city(city_name)
    self.manager.current = 'properties'
```

**New Method**: `PropertyListScreen.load_for_city(city_name)`
- Sets filter_city to selected city
- Sets property_type to 'longterm'
- Updates heading to "Long-term Properties in {city}"
- Calls `apply_filters_longterm()`

### 4. PropertyListScreen (Long-term Mode)
**Purpose**: Display properties filtered by city

**Dual Mode Support**:
- Student accommodations: `load_for_uni(uni_id, uni_name)`
- Long-term properties: `load_for_city(city_name)`

**API Endpoint**: `GET /api/properties/?property_type=longterm&min_price={}&max_price={}&order={}`

**Filtering**:
```python
# Server-side: property_type=longterm
# Client-side: Filter by city name
result = [p for p in result if p.get('city', '').lower() == self.filter_city.lower()]
```

**Property Cards**:
- Airbnb-style horizontal/vertical layout
- White background with rounded corners
- Property image (40% width horizontal, fixed height vertical)
- Title, city location (📍), description
- Price per month (large, bold)
- Property subtype badge (if available)
- Click to view details

### 5. PropertyListScreen → PropertyDetailScreen
**Trigger**: Click on property card

**Handler**: 
```python
def _open_detail(_instance, pid=p['id']):
    det = self.manager.get_screen('property_detail')
    det.load_property(pid)
    self.manager.current = 'property_detail'
```

### 6. PropertyDetailScreen
**Purpose**: Show full property details

**Features**:
- Property title, description
- Full image gallery
- Price information (per month for long-term)
- Location details
- Amenities and property info
- "Contact Landlord" button

### 7. PropertyDetailScreen → PropertyContactScreen
**Trigger**: Click "Contact Landlord" or "Proceed to Payment"

**Handler**: Opens contact/payment screen with property context

## Code Changes

### main.py Changes

#### 1. PropertyListScreen class variables:
```python
current_filters = {}
filter_city = None
property_type = None
```

#### 2. New Methods:
- `load_for_city(city_name)`: Initialize long-term mode with city filter
- `apply_filters_longterm()`: API call for long-term properties
- `on_loaded_longterm(req, result)`: Handle long-term property results with city filtering

#### 3. Enhanced Methods:
- `load_for_uni()`: Now resets filter_city and property_type
- Modified to support dual-mode operation

### LocationListScreen Enhancements

#### Modern Card Design:
```python
create_location_card(city_name, property_count, min_price, max_price, index)
```

**Features**:
- White card with gold border
- City name with location icon
- Property count display
- Price range badge
- Responsive heights and fonts
- Fade-in animation
- Click navigation to PropertyListScreen

## Responsive Design

### Breakpoints:
- **Small** (<600dp): 1 column, vertical cards, smaller fonts
- **Medium** (600-900dp): 2 columns, horizontal cards, medium fonts
- **Large** (≥900dp): 3 columns, horizontal cards, larger fonts

### Font Sizes:
- City name: sp(16-18)
- Property count: sp(12-13)
- Price badge: sp(11-12)
- Property titles: sp(15-17)
- Property descriptions: sp(12-13)

### Card Heights:
- LocationListScreen cards: 130dp (small) / 150dp (large)
- PropertyListScreen cards: 260dp (vertical) / 200dp (horizontal)

## API Integration

### Endpoints Used:
1. **Load Cities**: `GET /api/properties/?property_type=longterm`
2. **Load Properties**: `GET /api/properties/?property_type=longterm&min_price={}&max_price={}&order={}`
3. **Property Details**: `GET /api/properties/{id}/`

### Expected Response Format:

**Properties List**:
```json
{
  "results": [
    {
      "id": 1,
      "title": "Modern Apartment",
      "description": "...",
      "city": "New York",
      "price_per_month": 1500,
      "thumbnail": "...",
      "property_subtype": "Apartment",
      ...
    }
  ]
}
```

## Testing Flow

### Manual Test Steps:
1. Launch app
2. Click "Long-term accommodation" on HomeScreen
3. Verify LocationListScreen displays cities with:
   - Correct property counts
   - Correct price ranges
   - Modern card design
4. Click on a city
5. Verify PropertyListScreen shows:
   - Heading "Long-term Properties in {city}"
   - Only properties from selected city
   - Correct pricing (per month)
6. Click on a property
7. Verify PropertyDetailScreen loads correctly
8. Test contact/payment flow

## Future Enhancements

### Potential Additions:
- Filter by price range on LocationListScreen
- Sort cities by property count or price
- Show property thumbnails on LocationListScreen
- Add city description/info
- Property type filters (Apartment, House, Condo, etc.)
- Advanced search within PropertyListScreen
- Map view of properties in selected city
- Favorite/save properties functionality

## Design Consistency

### Matches Student Accommodation Pattern:
- **Student**: UniversitiesScreen → PropertyListScreen → Details → Contact
- **Long-term**: LocationListScreen → PropertyListScreen → Details → Contact

### Shared Components:
- PropertyListScreen (dual-mode: university/city filtering)
- PropertyDetailScreen (works for all property types)
- PropertyContactScreen (handles all contact/payment flows)
- Consistent header design across all screens
- Airbnb-inspired card layouts throughout
- Gold accent color (#FFD700)
- Responsive grid system

## Summary
The long-term accommodation flow is now complete and functional, providing users with an intuitive way to browse properties by city, view details, and proceed with contact/payment - mirroring the successful student accommodation flow design.

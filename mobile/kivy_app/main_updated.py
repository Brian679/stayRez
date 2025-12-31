from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line
import traceback
from datetime import datetime
import os
import json

API_BASE = "http://127.0.0.1:8000/api/"

# Token storage
token_store = JsonStore('user_tokens.json')


def get_auth_headers():
    """Get authentication headers with token if available"""
    if token_store.exists('auth'):
        token = token_store.get('auth').get('token')
        return {'Authorization': f'Bearer {token}'}
    return {}


def save_auth_token(token):
    """Save authentication token"""
    token_store.put('auth', token=token)


def clear_auth_token():
    """Clear authentication token"""
    if token_store.exists('auth'):
        token_store.delete('auth')


def start_pulse(widget, interval=0.6):
    """Start a simple opacity pulse on the given widget."""
    if widget is None:
        return
    if hasattr(widget, '_pulse_event') and widget._pulse_event:
        return
    def _tick(dt):
        widget.opacity = 0.35 if widget.opacity >= 1.0 else 1.0
    widget._pulse_event = Clock.schedule_interval(_tick, interval)


def stop_pulse(widget):
    """Stop pulsing and restore full opacity."""
    if widget is None:
        return
    if hasattr(widget, '_pulse_event') and widget._pulse_event:
        widget._pulse_event.cancel()
        widget._pulse_event = None
    widget.opacity = 1.0


def fade_in_widget(widget, delay=0.0, duration=0.28):
    widget.opacity = 0
    def _do(dt):
        Animation(opacity=1.0, d=duration).start(widget)
    Clock.schedule_once(_do, delay)


class HomeScreen(Screen):
    def on_pre_enter(self):
        print('HomeScreen on_pre_enter - loading services from API')
        self.load_services()
    
    def load_services(self):
        """Fetch services from API and build service tiles dynamically"""
        def on_success(req, result):
            print(f'Services loaded: {len(result)} services')
            grid = self.ids.services_grid
            grid.clear_widgets()
            
            if not isinstance(result, list):
                print('Error: Services API returned non-list:', type(result))
                return
            
            # Build service tiles from API data
            for idx, service in enumerate(result):
                tile = self.create_service_tile(service)
                grid.add_widget(tile)
                fade_in_widget(tile, delay=(idx * 0.06) + 0.12)
        
        def on_failure(req, error):
            print(f'Failed to load services: {error}')
            grid = self.ids.services_grid
            grid.clear_widgets()
            error_label = Label(
                text='Failed to load services.\\nPlease check your connection.',
                halign='center',
                color=(0.5, 0.5, 0.5, 1)
            )
            grid.add_widget(error_label)
        
        UrlRequest(
            API_BASE + 'services/',
            on_success=on_success,
            on_failure=on_failure,
            on_error=on_failure
        )
    
    def create_service_tile(self, service):
        """Create a service tile widget from service data"""
        # Parse colors
        bg_color = self.hex_to_rgba(service.get('background_color', '#eeeeee'))
        text_color = self.hex_to_rgba(service.get('text_color', '#333333'))
        
        # Create tile container
        tile = BoxLayout(
            orientation='vertical',
            padding=0,
            spacing=0,
            size_hint_y=None,
            height=dp(240)
        )
        
        # Add background
        with tile.canvas.before:
            Color(*bg_color)
            tile.bg_rect = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(10)])
        
        tile.bind(pos=lambda w, v: setattr(w.bg_rect, 'pos', v))
        tile.bind(size=lambda w, v: setattr(w.bg_rect, 'size', v))
        
        # Add image
        image_url = service.get('image') or f'assets/{service.get("slug", "students")}.png'
        img = AsyncImage(
            source=image_url,
            size_hint_y=None,
            height=dp(140)
        )
        tile.add_widget(img)
        
        # Add button with text
        btn_text = f"[b]{service['name']}[/b]\\n\\n{service.get('description', '')}"
        btn = Button(
            text=btn_text,
            markup=True,
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=text_color,
            font_size='13sp',
            halign='left',
            valign='top',
            padding=[dp(12), dp(8)]
        )
        btn.bind(size=btn.setter('text_size'))
        
        # Navigate based on property_type
        def on_tile_click(_):
            prop_type = service.get('property_type', '')
            if prop_type == 'students':
                self.manager.current = 'universities'
        
        btn.bind(on_release=on_tile_click)
        tile.add_widget(btn)
        
        return tile
    
    @staticmethod
    def hex_to_rgba(hex_color, alpha=1.0):
        """Convert hex color to RGBA tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b, alpha)
        except:
            return (0.93, 0.93, 0.93, alpha)


class UniversitiesScreen(Screen):
    def on_pre_enter(self):
        print('UniversitiesScreen on_pre_enter')
        self.ids.unis_container.clear_widgets()
        self.ids.loading_label.text = 'Loading...'
        start_pulse(self.ids.loading_label)
        
        UrlRequest(API_BASE + 'universities/', on_success=self.on_loaded, on_error=self.on_error, on_failure=self.on_error)

    def on_loaded(self, req, result):
        self.ids.loading_label.text = ''
        stop_pulse(self.ids.loading_label)
        self.ids.unis_container.clear_widgets()
        
        # Validate result is a list or dict with results key
        if isinstance(result, dict):
            result = result.get('results', [])
        elif not isinstance(result, list):
            error_label = Label(text=f'Error loading universities: {str(result)[:100]}', color=(0.8, 0.3, 0.3, 1))
            self.ids.unis_container.add_widget(error_label)
            return
            
        for idx, u in enumerate(result):
            class ClickableCard(ButtonBehavior, BoxLayout):
                pass
            
            card = ClickableCard(orientation='vertical', padding=dp(16), size_hint_y=None, spacing=dp(8))
            card.height = dp(180)
            card.opacity = 0
            
            # Add rounded background
            with card.canvas.before:
                Color(0.97, 0.97, 0.97, 1)
                card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10,])
            card.bind(pos=lambda instance, value, rect=card.bg_rect: setattr(rect, 'pos', value))
            card.bind(size=lambda instance, value, rect=card.bg_rect: setattr(rect, 'size', value))
            
            # University name
            name = Label(text=f"[b]{u.get('name')}[/b]", markup=True, size_hint_y=None, height=dp(32), 
                        font_size='18sp', halign='left', valign='top', color=(0, 0, 0, 1))
            name.bind(size=name.setter('text_size'))
            
            # City
            city_val = u.get('city')
            if isinstance(city_val, dict):
                city_name = city_val.get('name', '')
            else:
                city_name = ''
            try:
                fee = float(u.get('admin_fee_per_head') or 0)
            except Exception:
                fee = 0.0
            
            if city_name:
                meta = Label(text=f"[color=#6c757d]{city_name}[/color]", markup=True, size_hint_y=None, height=dp(24),
                            font_size='14sp', halign='left', valign='middle')
                meta.bind(size=meta.setter('text_size'))
                card.add_widget(name)
                card.add_widget(meta)
            else:
                card.add_widget(name)
            
            # Admin fee badge
            fee_label = Label(text=f"[b]Admin Fee: ${fee:.2f}[/b]", markup=True, size_hint_y=None, height=dp(26),
                            font_size='13sp', halign='left', valign='middle', color=(0.8, 0.5, 0, 1))
            fee_label.bind(size=fee_label.setter('text_size'))
            card.add_widget(fee_label)
            
            # Description
            desc = Label(text='Access landlord contacts for 3 properties per university after admin approval.', 
                        size_hint_y=None, height=dp(30), font_size='11sp', halign='left', valign='top', 
                        color=(0.5, 0.5, 0.5, 1))
            desc.bind(size=desc.setter('text_size'))
            card.add_widget(desc)
            
            # Make entire card clickable
            def _open_props(_instance, uni_id=u['id'], uni_name=u.get('name')):
                props_screen = self.manager.get_screen('properties')
                props_screen.load_for_uni(uni_id, uni_name)
                self.manager.current = 'properties'

            card.bind(on_release=_open_props)
            self.ids.unis_container.add_widget(card)
            fade_in_widget(card, delay=idx * 0.05)

    def on_error(self, req, error):
        self.ids.loading_label.text = ''
        stop_pulse(self.ids.loading_label)
        self.ids.unis_container.clear_widgets()
        self.ids.unis_container.add_widget(Label(text='Failed to load universities'))


class PropertyListScreen(Screen):
    def load_for_uni(self, uni_id, uni_name=None):
        self.uni_id = uni_id
        self.uni_name = uni_name or 'Properties'
        self.ids.props_heading.text = f"Properties for {self.uni_name}"
        self.ids.props_container.clear_widgets()
        self.ids.props_loading.text = 'Loading...'
        start_pulse(self.ids.props_loading)
        
        url = f"{API_BASE}universities/{uni_id}/properties/"
        UrlRequest(url, on_success=self.on_loaded, on_error=self.on_error, on_failure=self.on_error)

    def on_loaded(self, req, result):
        self.ids.props_loading.text = ''
        stop_pulse(self.ids.props_loading)
        self.ids.props_container.clear_widgets()
        
        # Validate result
        if isinstance(result, dict):
            result = result.get('results', [])
        elif not isinstance(result, list):
            empty_label = Label(text=f'Error loading properties: {str(result)[:100]}', color=(0.8, 0.3, 0.3, 1))
            self.ids.props_container.add_widget(empty_label)
            return
            
        if not result:
            empty_label = Label(text='No properties found', color=(0.5, 0.5, 0.5, 1))
            self.ids.props_container.add_widget(empty_label)
            return
        
        for idx, p in enumerate(result):
            class ClickableCard(ButtonBehavior, BoxLayout):
                pass
            
            # Responsive sizing based on screen width
            screen_width = Window.width
            is_small = screen_width < dp(600)
            card_orientation = 'vertical' if is_small else 'horizontal'
            card_height = dp(300) if is_small else dp(220)
            
            card = ClickableCard(orientation=card_orientation, size_hint_y=None, height=card_height, padding=0, spacing=0)
            card.opacity = 0
            
            # Add white background with shadow
            with card.canvas.before:
                Color(0, 0, 0, 0.05)
                card.shadow_rect = RoundedRectangle(pos=(card.x, card.y - dp(2)), size=card.size, radius=[dp(12),])
                Color(1, 1, 1, 1)
                card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12),])
                Color(0.92, 0.92, 0.92, 1)
            
            with card.canvas.after:
                card.border_line = Line(rounded_rectangle=[card.x, card.y, card.width, card.height, dp(12)], width=1)
            
            def update_card_graphics(instance, value):
                card.shadow_rect.pos = (instance.x, instance.y - dp(2))
                card.shadow_rect.size = instance.size
                card.bg_rect.pos = instance.pos
                card.bg_rect.size = instance.size
                card.border_line.rounded_rectangle = [instance.x, instance.y, instance.width, instance.height, dp(12)]
            
            card.bind(pos=update_card_graphics, size=update_card_graphics)
            
            # Image - left side for horizontal, top for vertical
            images = p.get('images', [])
            image_url = images[0].get('image') if images else ''
            
            if is_small:
                img = AsyncImage(source=image_url, size_hint_y=None, height=dp(180))
            else:
                img = AsyncImage(source=image_url, size_hint_x=0.4, size_hint_y=1)
            # Fill the image slot (like CSS object-fit: cover)
            if hasattr(img, 'fit_mode'):
                try:
                    img.fit_mode = 'cover'
                except Exception:
                    pass
            if hasattr(img, 'allow_stretch'):
                img.allow_stretch = True
            if hasattr(img, 'keep_ratio'):
                img.keep_ratio = False
            card.add_widget(img)
            
            # Content container
            content = BoxLayout(orientation='vertical', padding=[dp(16), dp(12)], spacing=dp(6))
            
            # Header: Title and Price
            header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(12))
            
            # Title section
            title_section = BoxLayout(orientation='vertical', spacing=dp(4))
            title = Label(
                text=f"[b]{p.get('title', 'Untitled')}[/b]", 
                markup=True, 
                font_size=sp(16), 
                halign='left', 
                valign='top', 
                color=(0.13, 0.13, 0.13, 1),
                size_hint_y=None,
                height=dp(24)
            )
            title.bind(size=title.setter('text_size'))
            title_section.add_widget(title)
            
            # Location/distance
            if p.get('distance_km'):
                location = Label(
                    text=f"[color=#717171]📍 {round(p.get('distance_km', 0), 1)} km from campus[/color]",
                    markup=True,
                    font_size=sp(12),
                    halign='left',
                    valign='top',
                    size_hint_y=None,
                    height=dp(18)
                )
                location.bind(size=location.setter('text_size'))
                title_section.add_widget(location)
            
            header.add_widget(title_section)
            
            # Price section
            price_section = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(90), spacing=dp(2))
            is_overnight = p.get('overnight', False)
            if is_overnight:
                price_text = f"${p.get('nightly_price', 'N/A')}"
                price_label_text = '[color=#717171]per night[/color]'
            else:
                price_text = f"${p.get('price_per_month', 'N/A')}"
                price_label_text = '[color=#717171]per month[/color]'
            
            price = Label(
                text=f"[b]{price_text}[/b]",
                markup=True,
                font_size=sp(20),
                halign='right',
                valign='top',
                color=(0.13, 0.13, 0.13, 1),
                size_hint_y=None,
                height=dp(26)
            )
            price.bind(size=price.setter('text_size'))
            
            price_label = Label(
                text=price_label_text,
                markup=True,
                font_size=sp(11),
                halign='right',
                valign='top',
                size_hint_y=None,
                height=dp(16)
            )
            price_label.bind(size=price_label.setter('text_size'))
            
            price_section.add_widget(price)
            price_section.add_widget(price_label)
            header.add_widget(price_section)
            
            content.add_widget(header)
            
            # Footer: Amenities badges
            footer = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(6))
            
            gender = p.get('gender_display', p.get('gender', ''))
            sharing = p.get('sharing_display', p.get('sharing', ''))
            
            if gender:
                gender_badge = Label(
                    text=f'[color=#222222]{gender}[/color]',
                    markup=True,
                    font_size=sp(11),
                    size_hint=(None, None),
                    size=(dp(70), dp(26)),
                    halign='center',
                    valign='middle'
                )
                gender_badge.bind(size=gender_badge.setter('text_size'))
                with gender_badge.canvas.before:
                    Color(0.97, 0.97, 0.97, 1)
                    gender_badge.bg = RoundedRectangle(pos=gender_badge.pos, size=gender_badge.size, radius=[dp(6),])
                gender_badge.bind(pos=lambda i, v, bg=gender_badge.bg: setattr(bg, 'pos', i.pos))
                gender_badge.bind(size=lambda i, v, bg=gender_badge.bg: setattr(bg, 'size', i.size))
                footer.add_widget(gender_badge)
            
            if sharing:
                sharing_badge = Label(
                    text=f'[color=#222222]{sharing}[/color]',
                    markup=True,
                    font_size=sp(11),
                    size_hint=(None, None),
                    size=(dp(80), dp(26)),
                    halign='center',
                    valign='middle'
                )
                sharing_badge.bind(size=sharing_badge.setter('text_size'))
                with sharing_badge.canvas.before:
                    Color(0.97, 0.97, 0.97, 1)
                    sharing_badge.bg = RoundedRectangle(pos=sharing_badge.pos, size=sharing_badge.size, radius=[dp(6),])
                sharing_badge.bind(pos=lambda i, v, bg=sharing_badge.bg: setattr(bg, 'pos', i.pos))
                sharing_badge.bind(size=lambda i, v, bg=sharing_badge.bg: setattr(bg, 'size', i.size))
                footer.add_widget(sharing_badge)
            
            if p.get('overnight'):
                overnight_badge = Label(
                    text='[color=#2e7d32]⭐ Overnight[/color]',
                    markup=True,
                    font_size=sp(11),
                    size_hint=(None, None),
                    size=(dp(90), dp(26)),
                    halign='center',
                    valign='middle'
                )
                overnight_badge.bind(size=overnight_badge.setter('text_size'))
                with overnight_badge.canvas.before:
                    Color(0.91, 0.96, 0.91, 1)
                    overnight_badge.bg = RoundedRectangle(pos=overnight_badge.pos, size=overnight_badge.size, radius=[dp(6),])
                overnight_badge.bind(pos=lambda i, v, bg=overnight_badge.bg: setattr(bg, 'pos', i.pos))
                overnight_badge.bind(size=lambda i, v, bg=overnight_badge.bg: setattr(bg, 'size', i.size))
                footer.add_widget(overnight_badge)
            
            footer.add_widget(BoxLayout())  # Spacer
            content.add_widget(footer)
            
            card.add_widget(content)
            
            # Make card clickable
            def _open_detail(_instance, pid=p['id']):
                det = self.manager.get_screen('property_detail')
                det.load_property(pid)
                self.manager.current = 'property_detail'

            card.bind(on_release=_open_detail)
            self.ids.props_container.add_widget(card)
            fade_in_widget(card, delay=idx * 0.05)

    def on_error(self, req, error):
        self.ids.props_loading.text = ''
        stop_pulse(self.ids.props_loading)
        self.ids.props_container.clear_widgets()
        self.ids.props_container.add_widget(Label(text='Failed to load properties'))


class PropertyDetailScreen(Screen):
    def load_property(self, prop_id):
        self.property_id = prop_id
        self.ids.prop_loading.text = 'Loading...'
        url = f"{API_BASE}properties/{prop_id}/"
        UrlRequest(url, on_success=self.on_loaded, on_error=self.on_error, on_failure=self.on_error)

    def on_loaded(self, req, result):
        self.ids.prop_loading.text = ''
        self.ids.prop_title.text = result.get('title', 'Property')
        self.ids.prop_description.text = result.get('description', '')
        
        # Build details text
        details = []
        if result.get('gender_display'):
            details.append(f"Gender: {result.get('gender_display')}")
        if result.get('sharing_display'):
            details.append(f"Sharing: {result.get('sharing_display')}")
        if result.get('max_occupancy'):
            details.append(f"Max Occupancy: {result.get('max_occupancy')}")
        if result.get('distance_km'):
            details.append(f"Distance: {round(result.get('distance_km'), 1)} km")
        
        self.ids.prop_details.text = ' • '.join(details)
        
        # Price
        if result.get('overnight'):
            self.ids.price_label.text = f"[b]${result.get('nightly_price', 'N/A')}[/b] per night"
        else:
            self.ids.price_label.text = f"[b]${result.get('price_per_month', 'N/A')}[/b] per month"
        
        # Images
        imgs = result.get('images') or []
        if imgs:
            self.ids.prop_image.source = imgs[0].get('image', '')
        else:
            self.ids.prop_image.source = ''

    def on_error(self, req, error):
        self.ids.prop_loading.text = ''
        self.ids.prop_title.text = 'Failed to load'
        self.ids.prop_description.text = ''
    
    def contact_landlord(self):
        """Handle contact landlord button click - requires login"""
        if not token_store.exists('auth'):
            # Not logged in - redirect to login
            self.manager.current = 'login'
            return
        
        # User is logged in - contact landlord
        url = f"{API_BASE}properties/{self.property_id}/contact/"
        headers = get_auth_headers()
        
        def on_success(req, result):
            # Show landlord contact info
            self.ids.contact_btn.text = 'Contact Info Unlocked!'
            self.ids.contact_btn.background_color = (0, 0.7, 0, 1)
        
        def on_error(req, error):
            self.ids.contact_btn.text = 'Failed - Try Again'
        
        UrlRequest(url, on_success=on_success, on_error=on_error, req_headers=headers)


class LoginScreen(Screen):
    def do_login(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        self.ids.error_label.text = 'Logging in...'
        
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'email': email, 'password': password})
        UrlRequest(
            API_BASE + 'auth/login/', 
            on_success=self.on_login_success, 
            on_error=self.on_login_error, 
            on_failure=self.on_login_error,
            req_body=data, 
            req_headers=headers, 
            method='POST'
        )
    
    def on_login_success(self, req, result):
        # Save token
        token = result.get('access') or result.get('token')
        if token:
            save_auth_token(token)
            self.ids.error_label.text = 'Login successful!'
            # Navigate back to home or previous screen
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'home'), 1.0)
        else:
            self.ids.error_label.text = 'Login failed - no token received'
    
    def on_login_error(self, req, error):
        self.ids.error_label.text = 'Login failed. Please check your credentials.'


class RegisterScreen(Screen):
    def do_register(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        password2 = self.ids.password2_input.text
        
        if password != password2:
            self.ids.error_label.text = 'Passwords do not match'
            return
        
        self.ids.error_label.text = 'Creating account...'
        
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'email': email,
            'password': password
        })
        UrlRequest(
            API_BASE + 'auth/register/', 
            on_success=self.on_register_success,
            on_error=self.on_register_error, 
            on_failure=self.on_register_error,
            req_body=data, 
            req_headers=headers, 
            method='POST'
        )
    
    def on_register_success(self, req, result):
        self.ids.error_label.text = 'Account created! Please login.'
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'login'), 1.5)
    
    def on_register_error(self, req, error):
        self.ids.error_label.text = 'Registration failed. Please try again.'


# Build KV string for UI
KV = '''
#:import dp kivy.metrics.dp

<HomeScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: 0.98, 0.98, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(8), dp(6)]
            spacing: dp(10)
            Label:
                text: '[b]off[/b][color=#ffd700]Rez[/color]'
                markup: True
                size_hint_x: None
                width: dp(120)
                font_size: dp(28)
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                color: 0, 0, 0, 1
            Widget:
            Button:
                text: 'Login'
                size_hint_x: None
                width: dp(70)
                background_normal: ''
                background_color: 0, 0, 0, 0
                color: 0, 0.4, 0.8, 1
                font_size: dp(14)
                on_release: app.root.current = 'login'
            Button:
                text: 'Register'
                size_hint_x: None
                width: dp(80)
                background_normal: ''
                color: 1, 1, 1, 1
                font_size: dp(14)
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8),]
                on_release: app.root.current = 'register'
        
        # Services grid
        ScrollView:
            GridLayout:
                id: services_grid
                cols: 2
                spacing: dp(10)
                padding: [dp(4), 0]
                size_hint_y: None
                height: self.minimum_height

<UniversitiesScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: 0.98, 0.98, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(4), dp(6)]
            spacing: dp(10)
            Button:
                text: '← Back'
                size_hint_x: None
                width: dp(80)
                background_normal: ''
                color: 0.2, 0.2, 0.2, 1
                font_size: dp(14)
                canvas.before:
                    Color:
                        rgba: 0.93, 0.93, 0.93, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8),]
                on_release: app.root.current = 'home'
            Label:
                text: '[b]Universities[/b]'
                markup: True
                font_size: dp(18)
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                color: 0, 0, 0, 1
            Label:
                id: loading_label
                text: ''
                size_hint_x: None
                width: dp(100)
                halign: 'right'
                valign: 'middle'
                color: 0.5, 0.5, 0.5, 1
                font_size: dp(12)
        
        ScrollView:
            GridLayout:
                id: unis_container
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [dp(4), dp(4)]

<PropertyListScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: 0.98, 0.98, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(4), dp(6)]
            spacing: dp(10)
            Button:
                text: '← Back'
                size_hint_x: None
                width: dp(80)
                background_normal: ''
                color: 0.2, 0.2, 0.2, 1
                font_size: dp(14)
                canvas.before:
                    Color:
                        rgba: 0.93, 0.93, 0.93, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8),]
                on_release: app.root.current = 'universities'
            Label:
                id: props_heading
                text: '[b]Properties[/b]'
                markup: True
                font_size: dp(18)
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                color: 0, 0, 0, 1
            Label:
                id: props_loading
                text: ''
                size_hint_x: None
                width: dp(100)
                halign: 'right'
                valign: 'middle'
                color: 0.5, 0.5, 0.5, 1
                font_size: dp(12)
        
        ScrollView:
            GridLayout:
                id: props_container
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [dp(4), dp(4)]

<PropertyDetailScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Header
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(12), dp(6)]
            spacing: dp(10)
            Button:
                text: '← Back'
                size_hint_x: None
                width: dp(80)
                background_normal: ''
                color: 0.2, 0.2, 0.2, 1
                font_size: dp(14)
                canvas.before:
                    Color:
                        rgba: 0.93, 0.93, 0.93, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8),]
                on_release: app.root.current = 'properties'
            Label:
                text: '[b]Property Details[/b]'
                markup: True
                font_size: dp(18)
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                color: 0, 0, 0, 1
            Label:
                id: prop_loading
                text: ''
                size_hint_x: None
                width: dp(100)
                halign: 'right'
                color: 0.5, 0.5, 0.5, 1
                font_size: dp(12)
        
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: dp(12)
                
                AsyncImage:
                    id: prop_image
                    size_hint_y: None
                    height: dp(300)
                
                Label:
                    id: prop_title
                    text: 'Property Title'
                    markup: True
                    font_size: dp(20)
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: 0, 0, 0, 1
                
                Label:
                    id: prop_description
                    text: 'Description'
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: 0.2, 0.2, 0.2, 1
                    font_size: dp(14)
                
                Label:
                    id: prop_details
                    text: 'Details'
                    markup: True
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: 0.2, 0.2, 0.2, 1
                    font_size: dp(14)
                
                Label:
                    id: price_label
                    text: 'Price: $0'
                    markup: True
                    font_size: dp(18)
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: 0, 0.5, 0, 1
                
                Button:
                    id: contact_btn
                    text: 'Contact Landlord'
                    size_hint_y: None
                    height: dp(48)
                    background_normal: ''
                    color: 1, 1, 1, 1
                    font_size: dp(16)
                    canvas.before:
                        Color:
                            rgba: 1, 0.84, 0, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(8),]
                    on_release: root.contact_landlord()

<LoginScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(16)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Widget:
            size_hint_y: 0.1
        
        BoxLayout:
            orientation: 'vertical'
            size_hint: (None, None)
            width: dp(400)
            height: self.minimum_height
            pos_hint: {'center_x': 0.5}
            spacing: dp(16)
            padding: dp(24)
            canvas.before:
                Color:
                    rgba: 0.98, 0.98, 0.98, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(12),]
            
            Label:
                text: '[b]off[/b][color=#ffd700]Rez[/color]'
                markup: True
                font_size: dp(36)
                size_hint_y: None
                height: dp(50)
                color: 0, 0, 0, 1
            
            Label:
                text: '[b]Login[/b]'
                markup: True
                font_size: dp(24)
                size_hint_y: None
                height: dp(40)
                color: 0, 0, 0, 1
            
            TextInput:
                id: email_input
                hint_text: 'Email'
                multiline: False
                size_hint_y: None
                height: dp(48)
                padding: [dp(12), dp(12)]
                background_normal: ''
                background_color: 1, 1, 1, 1
                foreground_color: 0, 0, 0, 1
                font_size: dp(16)
            
            TextInput:
                id: password_input
                hint_text: 'Password'
                password: True
                multiline: False
                size_hint_y: None
                height: dp(48)
                padding: [dp(12), dp(12)]
                background_normal: ''
                background_color: 1, 1, 1, 1
                foreground_color: 0, 0, 0, 1
                font_size: dp(16)
            
            Label:
                id: error_label
                text: ''
                color: 1, 0, 0, 1
                size_hint_y: None
                height: dp(20)
                font_size: dp(14)
            
            Button:
                text: 'Login'
                size_hint_y: None
                height: dp(48)
                background_normal: ''
                color: 1, 1, 1, 1
                font_size: dp(16)
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8),]
                on_release: root.do_login()
            
            BoxLayout:
                size_hint_y: None
                height: dp(30)
                Label:
                    text: "Don't have an account?"
                    color: 0.5, 0.5, 0.5, 1
                    font_size: dp(14)
                Button:
                    text: 'Register'
                    size_hint_x: None
                    width: dp(80)
                    background_normal: ''
                    background_color: 0, 0, 0, 0
                    color: 0, 0.4, 0.8, 1
                    font_size: dp(14)
                    on_release: app.root.current = 'register'
        
        Widget:
            size_hint_y: 0.2

<RegisterScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(16)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Widget:
            size_hint_y: 0.05
        
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint: (None, None)
                width: dp(400)
                height: self.minimum_height
                pos_hint: {'center_x': 0.5}
                spacing: dp(16)
                padding: dp(24)
                canvas.before:
                    Color:
                        rgba: 0.98, 0.98, 0.98, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(12),]
                
                Label:
                    text: '[b]off[/b][color=#ffd700]Rez[/color]'
                    markup: True
                    font_size: dp(36)
                    size_hint_y: None
                    height: dp(50)
                    color: 0, 0, 0, 1
                
                Label:
                    text: '[b]Create Account[/b]'
                    markup: True
                    font_size: dp(24)
                    size_hint_y: None
                    height: dp(40)
                    color: 0, 0, 0, 1
                
                TextInput:
                    id: email_input
                    hint_text: 'Email'
                    multiline: False
                    size_hint_y: None
                    height: dp(48)
                    padding: [dp(12), dp(12)]
                    background_normal: ''
                    background_color: 1, 1, 1, 1
                    foreground_color: 0, 0, 0, 1
                    font_size: dp(16)
                
                TextInput:
                    id: password_input
                    hint_text: 'Password'
                    password: True
                    multiline: False
                    size_hint_y: None
                    height: dp(48)
                    padding: [dp(12), dp(12)]
                    background_normal: ''
                    background_color: 1, 1, 1, 1
                    foreground_color: 0, 0, 0, 1
                    font_size: dp(16)
                
                TextInput:
                    id: password2_input
                    hint_text: 'Confirm Password'
                    password: True
                    multiline: False
                    size_hint_y: None
                    height: dp(48)
                    padding: [dp(12), dp(12)]
                    background_normal: ''
                    background_color: 1, 1, 1, 1
                    foreground_color: 0, 0, 0, 1
                    font_size: dp(16)
                
                Label:
                    id: error_label
                    text: ''
                    color: 1, 0, 0, 1
                    size_hint_y: None
                    height: dp(20)
                    font_size: dp(14)
                
                Button:
                    text: 'Register'
                    size_hint_y: None
                    height: dp(48)
                    background_normal: ''
                    color: 1, 1, 1, 1
                    font_size: dp(16)
                    canvas.before:
                        Color:
                            rgba: 0, 0, 0, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(8),]
                    on_release: root.do_register()
                
                BoxLayout:
                    size_hint_y: None
                    height: dp(30)
                    Label:
                        text: "Already have an account?"
                        color: 0.5, 0.5, 0.5, 1
                        font_size: dp(14)
                    Button:
                        text: 'Login'
                        size_hint_x: None
                        width: dp(70)
                        background_normal: ''
                        background_color: 0, 0, 0, 0
                        color: 0, 0.4, 0.8, 1
                        font_size: dp(14)
                        on_release: app.root.current = 'login'
        
        Widget:
            size_hint_y: 0.05
'''


class OffRezApp(App):
    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(UniversitiesScreen(name='universities'))
        sm.add_widget(PropertyListScreen(name='properties'))
        sm.add_widget(PropertyDetailScreen(name='property_detail'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.current = 'home'
        return sm


if __name__ == '__main__':
    OffRezApp().run()

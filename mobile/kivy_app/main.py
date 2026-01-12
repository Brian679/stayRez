from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.factory import Factory
from kivy.storage.jsonstore import JsonStore
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.properties import BooleanProperty, StringProperty
import traceback
from datetime import datetime
import os
import hashlib
import time
import urllib.parse
import webbrowser

API_BASE = "http://127.0.0.1:8000/api/"
API_AUTH_BASE = API_BASE + "auth/"

# Simple offline cache for GET responses. When online requests succeed we update
# the cache; when requests fail we fall back to the cached payload if present.
_CACHE_SCHEMA_VERSION = 1
_CACHE_PATH = os.path.join(os.path.dirname(__file__), 'offline_cache.json')
_CACHE = JsonStore(_CACHE_PATH)


class FormTextInput(TextInput):
    """TextInput tuned for forms inside ScrollViews.

    ScrollView can steal touch gestures on mobile, preventing focus/typing.
    By grabbing the touch when the field is hit, we ensure the TextInput
    receives the interaction and can focus properly.
    """

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.focus = True
            super().on_touch_down(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            super().on_touch_up(touch)
            return True
        return super().on_touch_up(touch)


Factory.register('FormTextInput', cls=FormTextInput)


def _cache_key(method: str, url: str) -> str:
    payload = f"v{_CACHE_SCHEMA_VERSION}:{method.upper()}:{url}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def cached_request(url, *, on_success, on_failure=None, method='GET', cache_fallback=True, cache_write=True, **kwargs):
    """UrlRequest wrapper with offline cache fallback for GET requests."""
    method_u = (method or 'GET').upper()
    key = _cache_key(method_u, url)

    def _on_success(req, result):
        if cache_write and method_u == 'GET':
            try:
                _CACHE.put(key, url=url, ts=time.time(), data=result)
            except Exception as e:
                print('Offline cache write failed:', e)
        on_success(req, result)

    def _on_failure(req, error):
        if cache_fallback and method_u == 'GET' and _CACHE.exists(key):
            try:
                cached = _CACHE.get(key)
                print(f"Offline cache hit: {cached.get('url', url)}")
                on_success(req, cached.get('data'))
                return
            except Exception as e:
                print('Offline cache read failed:', e)

        if on_failure:
            on_failure(req, error)
        else:
            print(f"Request failed: {url} -> {error}")

    UrlRequest(
        url,
        on_success=_on_success,
        on_error=_on_failure,
        on_failure=_on_failure,
        method=method,
        **kwargs,
    )

# If KV fails to load, a path to the error log will be stored here
KV_LOAD_ERROR = None


# KV paths. Loaded from inside OffRezApp.load_kv() to ensure `app.*` bindings
# in KV evaluate when the App instance exists.
KV_PATH = os.path.join(os.path.dirname(__file__), 'offrez.kv')
EXTRA_KV_PATH = os.path.join(os.path.dirname(__file__), 'screens_extra.kv')


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


def configure_cover_image(img):
    """Best-effort 'cover' image behavior (fill the box)."""
    if img is None:
        return
    # Newer Kivy
    if hasattr(img, 'fit_mode'):
        try:
            img.fit_mode = 'cover'
        except Exception:
            pass
        return

    # Older Kivy fallback
    if hasattr(img, 'allow_stretch'):
        img.allow_stretch = True
    if hasattr(img, 'keep_ratio'):
        img.keep_ratio = False


class HomeScreen(Screen):
    def show_options_menu(self):
        """Show options menu with navigation"""
        from kivy.uix.popup import Popup
        from kivy.uix.button import Button
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, RoundedRectangle
        
        menu_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        
        # Background
        with menu_layout.canvas.before:
            Color(1, 1, 1, 1)
            menu_layout.bg = RoundedRectangle(pos=menu_layout.pos, size=menu_layout.size, radius=[dp(12)])
        
        menu_layout.bind(pos=lambda w, v: setattr(w.bg, 'pos', v))
        menu_layout.bind(size=lambda w, v: setattr(w.bg, 'size', v))
        
        # Check if user is logged in
        session = SessionManager()
        is_logged_in = session.is_logged_in()
        
        def create_menu_button(text, on_click, bg_color=(0.95, 0.95, 0.95, 1)):
            """Create styled menu button"""
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(50),
                background_normal='',
                background_color=bg_color,
                color=[0.2, 0.2, 0.2, 1],
                font_size=sp(16),
                bold=False
            )
            btn.bind(on_release=on_click)
            return btn
        
        if is_logged_in:
            user = session.get_user()
            role = user.get('role', 'general')
            
            # User info header
            user_header = Label(
                text=f"[b]{user.get('email', 'User')}[/b]\\n{role.title()}",
                markup=True,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(15),
                color=[0.1, 0.1, 0.1, 1],
                halign='center',
                valign='middle'
            )
            user_header.bind(size=user_header.setter('text_size'))
            menu_layout.add_widget(user_header)
            
            # Divider
            divider = Widget(size_hint_y=None, height=dp(1))
            with divider.canvas:
                Color(0.85, 0.85, 0.85, 1)
                divider.line = RoundedRectangle(pos=divider.pos, size=divider.size)
            divider.bind(pos=lambda w, v: setattr(w.line, 'pos', v))
            divider.bind(size=lambda w, v: setattr(w.line, 'size', v))
            menu_layout.add_widget(divider)
            
            # Menu items
            menu_layout.add_widget(create_menu_button(
                '👤  Profile',
                lambda _: self.navigate_and_close('profile', popup)
            ))
            
            menu_layout.add_widget(create_menu_button(
                '🔔  Notifications',
                lambda _: self.navigate_and_close('notifications', popup)
            ))
            
            # My Properties (for landlords)
            if role == 'landlord':
                menu_layout.add_widget(create_menu_button(
                    '🏠  My Properties',
                    lambda _: self.navigate_and_close('my_properties', popup)
                ))
            
            menu_layout.add_widget(create_menu_button(
                '🏠  Home',
                lambda _: self.navigate_and_close('home', popup)
            ))

            menu_layout.add_widget(create_menu_button(
                'ℹ️  About us',
                lambda _: (popup.dismiss(), App.get_running_app().open_about())
            ))

            menu_layout.add_widget(create_menu_button(
                '✉️  Contact us',
                lambda _: (popup.dismiss(), App.get_running_app().open_contact())
            ))
            
            # Logout with different styling
            menu_layout.add_widget(create_menu_button(
                '🚪  Logout',
                lambda _: self.logout_and_close(popup),
                bg_color=(0.95, 0.2, 0.2, 0.15)
            ))
        else:
            # Welcome header
            welcome = Label(
                text='[b]Welcome to offRez[/b]',
                markup=True,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=[1, 0.85, 0, 1],
                bold=True
            )
            menu_layout.add_widget(welcome)
            
            # Login/Register options
            menu_layout.add_widget(create_menu_button(
                '🔑  Login',
                lambda _: self.navigate_and_close('login', popup),
                bg_color=(1, 0.85, 0, 0.2)
            ))
            
            menu_layout.add_widget(create_menu_button(
                '📝  Register',
                lambda _: self.navigate_and_close('register', popup),
                bg_color=(0.2, 0.6, 1, 0.2)
            ))

            menu_layout.add_widget(create_menu_button(
                'ℹ️  About us',
                lambda _: (popup.dismiss(), App.get_running_app().open_about()),
                bg_color=(0.95, 0.95, 0.95, 1)
            ))

            menu_layout.add_widget(create_menu_button(
                '✉️  Contact us',
                lambda _: (popup.dismiss(), App.get_running_app().open_contact()),
                bg_color=(0.95, 0.95, 0.95, 1)
            ))
        
        # Close button
        menu_layout.add_widget(Widget(size_hint_y=0.2))
        menu_layout.add_widget(create_menu_button(
            '✕  Close',
            lambda _: popup.dismiss(),
            bg_color=(0.9, 0.9, 0.9, 1)
        ))
        
        popup = Popup(
            title='',
            content=menu_layout,
            size_hint=(0.85, 0.75),
            auto_dismiss=True,
            separator_height=0,
            background='',
            background_color=[0, 0, 0, 0.7]
        )
        popup.open()
    
    def navigate_and_close(self, screen_name, popup):
        """Navigate to screen and close popup"""
        popup.dismiss()
        self.manager.current = screen_name
    
    def logout_and_close(self, popup):
        """Logout user and close popup"""
        session = SessionManager()
        session.clear_user()
        popup.dismiss()
        # Optionally reload home screen
        self.on_pre_enter()
    
    def on_pre_enter(self):
        print('HomeScreen on_pre_enter - loading services from API')
        try:
            self.manager.current = 'home'
        except Exception:
            pass
        
        # Load services from API
        self.load_services()
    
    def load_services(self):
        """Fetch services from API and build service tiles dynamically"""
        def on_success(req, result):
            print(f'Services loaded: {len(result)} services')
            if not hasattr(self.ids, 'services_grid'):
                print('Error: services_grid not found in KV')
                return
            
            grid = self.ids.services_grid
            grid.clear_widgets()
            
            # Validate result is a list
            if not isinstance(result, list):
                print('Error: Services API returned non-list:', type(result))
                return
            
            # Build service tiles from API data
            for idx, service in enumerate(result):
                tile = self.create_service_tile(service)
                grid.add_widget(tile)
                fade_in_widget(tile, delay=(idx * 0.06) + 0.12)
            
            # Animate brand/logo after services load
            if hasattr(self.ids, 'brand_logo'):
                self.ids.brand_logo.opacity = 0
                fade_in_widget(self.ids.brand_logo, delay=0.0)
        
        def on_failure(req, error):
            print(f'Failed to load services: {error}')
            if not hasattr(self.ids, 'services_grid'):
                return
            # Fallback: show error message
            grid = self.ids.services_grid
            grid.clear_widgets()
            error_label = Label(
                text='Failed to load services.\\nPlease check your connection.',
                halign='center',
                color=(0.5, 0.5, 0.5, 1)
            )
            grid.add_widget(error_label)
        
        cached_request(
            API_BASE + 'services/',
            on_success=on_success,
            on_failure=on_failure,
        )
    
    def create_service_tile(self, service):
        """Create a clickable service tile widget from service data"""
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.anchorlayout import AnchorLayout
        
        # Create clickable tile container using ButtonBehavior
        class ClickableTile(ButtonBehavior, BoxLayout):
            pass

        # Web-style service card (matches templates/web/home.html):
        # - black background
        # - image top half with light gray fallback background
        # - gold title, whitesmoke description
        # - responsive aspect ratio similar to CSS breakpoints
        tile = ClickableTile(
            orientation='vertical',
            padding=0,
            spacing=0,
            size_hint_y=None,
        )

        from kivy.graphics import Color, RoundedRectangle
        with tile.canvas.before:
            # Subtle shadow
            Color(0, 0, 0, 0.12)
            tile.shadow = RoundedRectangle(pos=(tile.x + dp(2), tile.y - dp(2)), size=tile.size, radius=[dp(10)])
            # Card background
            Color(0, 0, 0, 1)
            tile.bg_rect = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(10)])

        def _update_tile_canvas(w, _):
            tile.shadow.pos = (w.x + dp(2), w.y - dp(2))
            tile.shadow.size = w.size
            tile.bg_rect.pos = w.pos
            tile.bg_rect.size = w.size

        tile.bind(pos=_update_tile_canvas)
        tile.bind(size=_update_tile_canvas)

        def _apply_aspect_ratio(*_args):
            # Similar to CSS:
            # - small screens: 1 / 1.15 (taller)
            # - large screens: 1 / 0.9 (slightly shorter)
            ratio = 1.15 if Window.width < dp(600) else 0.9
            if tile.width > 0:
                tile.height = tile.width / ratio

        tile.bind(width=lambda *_: _apply_aspect_ratio())
        Clock.schedule_once(lambda *_: _apply_aspect_ratio(), 0)

        # Image container (top 50%) with light gray background (like .service-card-img)
        image_container = AnchorLayout(size_hint_y=0.5)
        with image_container.canvas.before:
            Color(0.94, 0.94, 0.94, 1)
            image_container.bg = RoundedRectangle(pos=image_container.pos, size=image_container.size, radius=[0, 0, 0, 0])

        def _update_img_bg(w, _):
            image_container.bg.pos = w.pos
            image_container.bg.size = w.size

        image_container.bind(pos=_update_img_bg)
        image_container.bind(size=_update_img_bg)

        image_url = service.get('image_url') or f'assets/{service.get("slug", "students")}.png'
        img = AsyncImage(source=image_url)
        configure_cover_image(img)
        image_container.add_widget(img)
        tile.add_widget(image_container)

        # Body (bottom 50%)
        body = BoxLayout(
            orientation='vertical',
            padding=[dp(14), dp(12)],
            spacing=dp(6),
            size_hint_y=0.5,
        )

        is_small = Window.width < dp(576)
        is_large = Window.width >= dp(992)
        title = Label(
            text=service.get('name', ''),
            bold=True,
            color=(1, 0.843, 0, 1),  # #ffd700
            font_size=sp(14) if is_small else (sp(15) if not is_large else sp(15)),
            halign='center' if is_small else 'left',
            valign='top',
            size_hint_y=None,
        )
        title.bind(size=title.setter('text_size'))
        if hasattr(title, 'max_lines'):
            title.max_lines = 2

        desc = Label(
            text=service.get('description', '') or '',
            color=(0.96, 0.96, 0.96, 1),  # whitesmoke-ish
            font_size=sp(11) if is_small else (sp(12) if not is_large else sp(11)),
            halign='center' if is_small else 'left',
            valign='top',
        )
        desc.bind(size=desc.setter('text_size'))

        # Apply web-like padding/line clamps at breakpoints
        def _apply_body_style(*_):
            small = Window.width < dp(576)
            large = Window.width >= dp(992)

            # Web: body padding ~14px, large screens ~10px
            body.padding = [dp(10), dp(10)] if large else [dp(14), dp(12)]

            title.halign = 'center' if small else 'left'
            desc.halign = 'center' if small else 'left'

            # Web: large screens clamp description to 2 lines
            if hasattr(desc, 'max_lines'):
                desc.max_lines = 3 if not large else 2
            if hasattr(title, 'max_lines'):
                title.max_lines = 2

            # Re-apply text_size for halign/valign
            title.text_size = title.size
            desc.text_size = desc.size

        tile.bind(size=_apply_body_style)
        Clock.schedule_once(lambda *_: _apply_body_style(), 0)

        # Make title take natural height based on font size
        title.height = max(dp(22), title.font_size * 1.6)

        body.add_widget(title)
        body.add_widget(desc)
        tile.add_widget(body)
        
        # Navigate based on property_type when entire tile is clicked
        def on_tile_click(_):
            prop_type = service.get('property_type', '')
            slug = service.get('slug', '')
            
            if prop_type == 'students' or slug == 'students':
                self.manager.current = 'universities'
            elif prop_type == 'longterm' or slug == 'longterm':
                self.manager.current = 'location_list'
            elif prop_type == 'shortterm' or slug == 'shortterm':
                self.manager.current = 'short_term'
            elif prop_type == 'realestate' or slug == 'realestate':
                self.manager.current = 'real_estate'
            elif slug == 'resorts':
                self.manager.current = 'resorts'
            elif slug == 'shops':
                self.manager.current = 'shops'
            else:
                print(f'Service clicked: {service["name"]}')
        
        tile.bind(on_release=on_tile_click)
        
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
            return (0.93, 0.93, 0.93, alpha)  # default gray


class UniversitiesScreen(Screen):
    def show_options_menu(self):
        """Show options menu - reuse from HomeScreen"""
        home_screen = self.manager.get_screen('home')
        home_screen.show_options_menu()
    
    def on_pre_enter(self):
        print('UniversitiesScreen on_pre_enter')
        # clear container and show loading state
        if hasattr(self.ids, 'unis_container'):
            self.ids.unis_container.clear_widgets()
        if hasattr(self.ids, 'loading_label'):
            self.ids.loading_label.text = 'Loading...'
            start_pulse(self.ids.loading_label)
        # Keep the subtitle (web-like) stable if present
        if hasattr(self.ids, 'subtitle_label'):
            self.ids.subtitle_label.text = 'Select a university to view available accommodations.'
        # if we previously had a KV load error, show a hint
        if KV_LOAD_ERROR and hasattr(self.ids, 'loading_label'):
            self.ids.loading_label.text += ' (KV loaded with errors, see logs)'
        cached_request(API_BASE + 'universities/', on_success=self.on_loaded, on_failure=self.on_error)

    def on_loaded(self, req, result):
        if hasattr(self.ids, 'loading_label'):
            self.ids.loading_label.text = ''
            stop_pulse(self.ids.loading_label)
        if not hasattr(self.ids, 'unis_container'):
            return
        self.ids.unis_container.clear_widgets()
        
        # Validate result is a list or dict with results key
        if isinstance(result, dict):
            result = result.get('results', [])
        elif not isinstance(result, list):
            error_label = Label(text=f'Error loading universities: {str(result)[:100]}', color=(0.8, 0.3, 0.3, 1))
            self.ids.unis_container.add_widget(error_label)
            return
            
        for idx, u in enumerate(result):
            card = self.create_university_card(u, idx)
            self.ids.unis_container.add_widget(card)
    
    def create_university_card(self, university, index):
        """Create a university card matching the web universities.html layout."""
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, RoundedRectangle

        class UniversityCard(ButtonBehavior, BoxLayout):
            pass

        w = Window.width
        # Card height similar to the web tile feel (compact but readable)
        card_height = dp(150) if w <= dp(576) else (dp(160) if w <= dp(768) else dp(170))

        card = UniversityCard(
            orientation='vertical',
            padding=[dp(16), dp(14)],
            spacing=dp(10),
            size_hint_y=None,
            height=card_height,
        )
        card.opacity = 0

        # Grey card background + subtle shadow (web: #f7f7f7, radius 10)
        with card.canvas.before:
            Color(0, 0, 0, 0.06)
            card.shadow = RoundedRectangle(pos=(card.x, card.y - dp(2)), size=card.size, radius=[dp(10)])
            Color(0.968, 0.968, 0.968, 1)  # ~#f7f7f7
            card.bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])

        def _sync_bg(inst, _):
            card.shadow.pos = (inst.x, inst.y - dp(2))
            card.shadow.size = inst.size
            card.bg.pos = inst.pos
            card.bg.size = inst.size

        card.bind(pos=_sync_bg, size=_sync_bg)

        # University name (centered, bold, responsive)
        uni_name = university.get('name', 'University')
        name_size = sp(16) if w <= dp(576) else (sp(18) if w <= dp(768) else (sp(20) if w <= dp(992) else sp(22)))
        name_label = Label(
            text=f"[b]{uni_name}[/b]",
            markup=True,
            font_size=name_size,
            color=(0.07, 0.07, 0.07, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(56),
        )
        name_label.bind(size=name_label.setter('text_size'))
        card.add_widget(name_label)

        # City (muted). Web shows just the city name (no prefix).
        # Avoid rendering numeric `city` ids.
        city_name = (university.get('city_name') or '').strip()
        if not city_name:
            city_val = university.get('city')
            if isinstance(city_val, dict):
                city_name = (city_val.get('name') or '').strip()
            else:
                city_name = ''

        if city_name:
            city_size = sp(13) if w <= dp(576) else (sp(14) if w <= dp(768) else sp(16))
            city_label = Label(
                text=city_name,
                font_size=city_size,
                color=(0.45, 0.45, 0.45, 1),
                halign='left',
                valign='middle',
                size_hint_y=None,
                height=dp(22),
            )
            city_label.bind(size=city_label.setter('text_size'))
            card.add_widget(city_label)

        # Admin Fee row: "Admin Fee:" + yellow badge like Bootstrap bg-warning
        try:
            fee = float(university.get('admin_fee_per_head') or 0)
        except Exception:
            fee = 0.0

        fee_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(10))

        fee_label = Label(
            text='[b]Admin Fee:[/b]',
            markup=True,
            font_size=sp(13) if w <= dp(576) else sp(14),
            color=(0.12, 0.12, 0.12, 1),
            halign='left',
            valign='middle',
            size_hint_x=None,
            width=dp(92),
        )
        fee_label.bind(size=fee_label.setter('text_size'))
        fee_row.add_widget(fee_label)

        badge = Label(
            text=f"[b]${fee:.2f}[/b]",
            markup=True,
            font_size=sp(13) if w <= dp(576) else sp(14),
            color=(0, 0, 0, 1),
            halign='center',
            valign='middle',
            size_hint=(None, None),
            size=(dp(92), dp(26)),
        )
        badge.bind(size=badge.setter('text_size'))

        with badge.canvas.before:
            Color(1, 0.84, 0, 1)  # #ffd700
            badge.bg = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(8)])

        badge.bind(pos=lambda inst, v: setattr(inst.bg, 'pos', v))
        badge.bind(size=lambda inst, v: setattr(inst.bg, 'size', v))
        fee_row.add_widget(badge)
        fee_row.add_widget(Widget())
        card.add_widget(fee_row)

        def on_card_click(_):
            props_screen = self.manager.get_screen('properties')
            props_screen.load_for_uni(university['id'], university.get('name'))
            self.manager.current = 'properties'

        card.bind(on_release=on_card_click)
        fade_in_widget(card, delay=index * 0.05)
        return card

    def on_error(self, req, error):
        if hasattr(self.ids, 'loading_label'):
            self.ids.loading_label.text = ''
            stop_pulse(self.ids.loading_label)
        if hasattr(self.ids, 'unis_container'):
            self.ids.unis_container.clear_widgets()
            self.ids.unis_container.add_widget(Label(text='Failed to load universities'))
        else:
            # Fallback if KV didn't create the container
            print('UniversitiesScreen: falling back to simple list')
            bl = BoxLayout(orientation='vertical', padding=12, spacing=8)
            bl.add_widget(Label(text='Universities (offline fallback)'))
            btn = Button(text='Back to Home', size_hint_y=None, height=40)
            btn.bind(on_release=lambda *_: setattr(self.manager, 'current', 'home'))
            bl.add_widget(btn)
            self.clear_widgets()
            self.add_widget(bl)


class PropertyListScreen(Screen):
    current_filters = {}
    filter_city = None
    filter_city_id = None
    property_type = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.liked_store = JsonStore('liked_properties.json')

    def is_liked(self, prop_id):
        return str(prop_id) in self.liked_store

    def toggle_like(self, prop, btn):
        prop_id = str((prop or {}).get('id'))
        if not prop_id or prop_id == 'None':
            return

        if self.is_liked(prop_id):
            self.liked_store.delete(prop_id)
            btn.text = '♡'
            btn.color = [0.25, 0.25, 0.25, 1]
        else:
            self.liked_store.put(prop_id, liked=True, prop=prop)
            btn.text = '♥'
            btn.color = [1, 0.2, 0.2, 1]

    def _create_web_like_property_card(self, prop, index=0):
        """Build a web-like accommodation card.

        Mirrors backend/templates/web/university_properties.html (.accommodation-card)
        as closely as Kivy allows (rounded card, header/meta/like, main image,
        title+price pill, description + read more, reaction pills).
        """
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, RoundedRectangle, Line
        from kivy.graphics import StencilPush, StencilUse, StencilUnUse, StencilPop

        class Card(ButtonBehavior, BoxLayout):
            pass

        w = float(Window.width or 0)
        is_small = w < dp(600)

        def _fsp(small_sp, large_sp):
            return sp(small_sp) if is_small else sp(large_sp)

        # Match web clamp(200px, 32vh, 280px)
        media_h = max(dp(200), min(dp(280), dp((Window.height or 0) * 0.32)))

        def _truncate(text, limit):
            t = '' if text is None else str(text)
            if len(t) <= limit:
                return t
            return t[: max(0, limit - 3)] + '...'

        def _display_gender(value):
            mapping = {
                'all': 'All',
                'boys': 'Boys only',
                'girls': 'Girls only',
                'mixed': 'Mixed Gender',
            }
            v = '' if value is None else str(value)
            return mapping.get(v, v)

        def _display_sharing(value):
            mapping = {
                'single': 'Single room',
                'two': '2 Sharing',
                'other': 'Other',
            }
            v = '' if value is None else str(value)
            return mapping.get(v, v)

        def _as_money(value):
            if value in (None, ''):
                return None
            try:
                # Keep integers clean, decimals stable.
                v = float(value)
                if v.is_integer():
                    return str(int(v))
                return f"{v:.2f}".rstrip('0').rstrip('.')
            except Exception:
                return str(value)

        def _make_rounded_media(source, radius_dp, *, height):
            holder = BoxLayout(size_hint_y=None, height=height)
            holder.padding = 0
            holder.spacing = 0
            holder.cla = None

            with holder.canvas.before:
                StencilPush()
                holder.clip_rect = RoundedRectangle(pos=holder.pos, size=holder.size, radius=[dp(radius_dp)])
                StencilUse()

            img = AsyncImage(source=source)
            configure_cover_image(img)
            holder.add_widget(img)

            with holder.canvas.after:
                StencilUnUse()
                RoundedRectangle(pos=holder.pos, size=holder.size, radius=[dp(radius_dp)])
                StencilPop()
                # web border: #f1ebe2
                Color(0.945, 0.922, 0.886, 1)
                holder.bd = Line(rounded_rectangle=[holder.x, holder.y, holder.width, holder.height, dp(radius_dp)], width=1)

            def _sync(_inst, _val):
                holder.clip_rect.pos = holder.pos
                holder.clip_rect.size = holder.size
                if hasattr(holder, 'bd'):
                    holder.bd.rounded_rectangle = [holder.x, holder.y, holder.width, holder.height, dp(radius_dp)]

            holder.bind(pos=_sync, size=_sync)
            return holder

        # Card
        card = Card(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(16), dp(14), dp(16), dp(16)],
            spacing=dp(12),
        )
        card.opacity = 0

        # Web colors
        border_rgba = (0.937, 0.902, 0.851, 1)  # #efe6d9
        with card.canvas.before:
            Color(1, 1, 1, 1)
            card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(22)])
        with card.canvas.after:
            Color(*border_rgba)
            card.border_line = Line(rounded_rectangle=[card.x, card.y, card.width, card.height, dp(22)], width=1)

        def _sync_card(_inst, _val):
            card.bg_rect.pos = card.pos
            card.bg_rect.size = card.size
            card.border_line.rounded_rectangle = [card.x, card.y, card.width, card.height, dp(22)]

        card.bind(pos=_sync_card, size=_sync_card)

        # Header
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(52) if is_small else dp(56),
            spacing=dp(12),
        )

        thumb = (prop or {}).get('thumbnail') or ''
        avatar = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)))
        with avatar.canvas.before:
            # #fff9f2 background + #e0d8c7 border
            Color(1, 0.976, 0.949, 1)
            avatar.bg = RoundedRectangle(pos=avatar.pos, size=avatar.size, radius=[dp(14)])
            Color(0.878, 0.847, 0.780, 1)
            avatar.bd = Line(rounded_rectangle=[avatar.x, avatar.y, avatar.width, avatar.height, dp(14)], width=2)
        avatar.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
        avatar.bind(size=lambda i, v: setattr(i.bg, 'size', v))
        avatar.bind(pos=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(14)]))
        avatar.bind(size=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(14)]))

        if thumb:
            avatar_media = _make_rounded_media(thumb, 14, height=avatar.height)
            avatar.add_widget(avatar_media)
        else:
            ph = Label(text='🏠', font_size=_fsp(16, 18), color=(0.62, 0.58, 0.54, 1), halign='center', valign='middle')
            ph.bind(size=ph.setter('text_size'))
            avatar.add_widget(ph)

        header.add_widget(avatar)

        # Meta
        meta = BoxLayout(orientation='vertical', spacing=dp(2))
        meta.size_hint_x = 1

        location = (prop or {}).get('location')
        city_name = (prop or {}).get('city_name')
        distance_km = (prop or {}).get('distance_km')
        if location:
            channel_text = str(location)
        elif city_name:
            channel_text = str(city_name)
        elif distance_km not in (None, ''):
            channel_text = f"{distance_km} km from campus"
        else:
            channel_text = 'Around campus'

        channel = Label(
            text=channel_text,
            font_size=_fsp(14, 15),
            bold=True,
            color=(0.114, 0.114, 0.122, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(20),
        )
        if hasattr(channel, 'shorten'):
            channel.shorten = True
            channel.shorten_from = 'right'
        channel.bind(size=channel.setter('text_size'))
        meta.add_widget(channel)

        gender_disp = (prop or {}).get('gender_display') or _display_gender((prop or {}).get('gender'))
        sharing_disp = (prop or {}).get('sharing_display') or _display_sharing((prop or {}).get('sharing'))
        followers_text = " · ".join([t for t in [gender_disp, sharing_disp] if t])

        followers = Label(
            text=followers_text,
            font_size=_fsp(11.5, 12.5),
            color=(0.545, 0.545, 0.561, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(16),
        )
        if hasattr(followers, 'shorten'):
            followers.shorten = True
            followers.shorten_from = 'right'
        followers.bind(size=followers.setter('text_size'))
        meta.add_widget(followers)

        header.add_widget(meta)

        # Like button (web: 38x38, circle, ♡ / ♥)
        like_btn = Button(
            text='♥' if self.is_liked((prop or {}).get('id')) else '♡',
            size_hint=(None, None),
            size=(dp(38), dp(38)),
            background_normal='',
            background_color=(0, 0, 0, 0),
            font_size=_fsp(16, 18),
            color=[1, 0.353, 0.373, 1] if self.is_liked((prop or {}).get('id')) else [0.25, 0.25, 0.25, 1],
        )
        with like_btn.canvas.before:
            Color(1, 1, 1, 1)
            like_btn.bg = RoundedRectangle(pos=like_btn.pos, size=like_btn.size, radius=[dp(999)])
            # subtle border
            Color(0.93, 0.93, 0.93, 1)
            like_btn.bd = Line(rounded_rectangle=[like_btn.x, like_btn.y, like_btn.width, like_btn.height, dp(999)], width=1)

        like_btn.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
        like_btn.bind(size=lambda i, v: setattr(i.bg, 'size', v))
        like_btn.bind(pos=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))
        like_btn.bind(size=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))
        like_btn.bind(on_release=lambda btn, p=prop: self.toggle_like(p, btn))

        header.add_widget(like_btn)
        card.add_widget(header)

        # Main media (rounded 16)
        img_src = (prop or {}).get('thumbnail') or 'assets/placeholder.png'
        media = _make_rounded_media(img_src, 16, height=media_h)
        card.add_widget(media)

        # Body
        body = BoxLayout(orientation='vertical', spacing=dp(6))

        title_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(10))
        prop_title = str((prop or {}).get('title') or 'Accommodation')
        title_lbl = Label(
            text=prop_title,
            font_size=_fsp(15, 16),
            bold=True,
            color=(0.122, 0.125, 0.137, 1),
            halign='left',
            valign='middle',
        )
        if hasattr(title_lbl, 'shorten'):
            title_lbl.shorten = True
            title_lbl.shorten_from = 'right'
        title_lbl.bind(size=title_lbl.setter('text_size'))
        title_row.add_widget(title_lbl)

        overnight = bool((prop or {}).get('overnight'))
        monthly = _as_money((prop or {}).get('price_per_month'))
        nightly = _as_money((prop or {}).get('nightly_price'))

        if overnight and nightly is not None:
            price_text = f"🔥 ${nightly} /night"
        elif monthly is not None:
            price_text = f"🔥 ${monthly} /month"
        else:
            price_text = "🔥 N/A"

        price_pill = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            height=dp(26),
            padding=[dp(12), dp(5), dp(12), dp(5)],
        )
        price_pill_lbl = Label(
            text=price_text,
            font_size=_fsp(11.5, 12.5),
            bold=True,
            color=(0.133, 0.133, 0.133, 1),
            halign='center',
            valign='middle',
        )
        price_pill_lbl.bind(size=price_pill_lbl.setter('text_size'))
        price_pill.add_widget(price_pill_lbl)

        def _sync_pill(_inst, _val):
            w = (price_pill_lbl.texture_size[0] or 0) + dp(24)
            price_pill.width = max(dp(90), min(w, dp(170)))
            price_pill_lbl.text_size = (price_pill.width - (price_pill.padding[0] + price_pill.padding[2]), None)

        price_pill_lbl.bind(texture_size=_sync_pill)
        _sync_pill(None, None)

        with price_pill.canvas.before:
            Color(1, 0.976, 0.953, 1)  # #fff9f3
            price_pill.bg = RoundedRectangle(pos=price_pill.pos, size=price_pill.size, radius=[dp(999)])
            Color(1, 0.894, 0.776, 1)  # #ffe4c6
            price_pill.bd = Line(rounded_rectangle=[price_pill.x, price_pill.y, price_pill.width, price_pill.height, dp(999)], width=1)

        price_pill.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
        price_pill.bind(size=lambda i, v: setattr(i.bg, 'size', v))
        price_pill.bind(pos=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))
        price_pill.bind(size=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))

        title_row.add_widget(price_pill)
        body.add_widget(title_row)

        desc = _truncate((prop or {}).get('description') or '', 110)
        if desc:
            desc_lbl = Label(
                text=desc,
                font_size=_fsp(12.5, 13.5),
                color=(0.290, 0.290, 0.310, 1),
                halign='left',
                valign='top',
                size_hint_y=None,
            )
            desc_lbl.bind(size=desc_lbl.setter('text_size'))

            def _sync_desc(_inst, _val):
                desc_lbl.text_size = (body.width, None)
                # aim for ~3 lines max
                desc_lbl.height = min(desc_lbl.texture_size[1] or dp(20), dp(66) if is_small else dp(74))

            desc_lbl.bind(texture_size=_sync_desc)
            body.bind(size=_sync_desc)
            body.add_widget(desc_lbl)

        read_more = Label(
            text='Read more',
            font_size=_fsp(11.5, 12.5),
            bold=True,
            color=(0.051, 0.431, 0.992, 1),  # #0d6efd
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(16),
        )
        read_more.bind(size=read_more.setter('text_size'))
        body.add_widget(read_more)

        # Reactions (web: sharing + max occupancy)
        reactions = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(8))
        pill_count = 0

        def _pill(text):
            pill = BoxLayout(
                orientation='horizontal',
                size_hint=(None, None),
                height=dp(28),
                padding=[dp(12), dp(5), dp(12), dp(5)],
            )
            lbl = Label(
                text=text,
                font_size=_fsp(11.5, 12.5),
                bold=True,
                color=(0.133, 0.133, 0.133, 1),
                halign='center',
                valign='middle',
            )
            lbl.bind(size=lbl.setter('text_size'))
            pill.add_widget(lbl)

            def _sync(_inst, _val):
                w = (lbl.texture_size[0] or 0) + dp(24)
                pill.width = max(dp(92), min(w, dp(190)))
                lbl.text_size = (pill.width - (pill.padding[0] + pill.padding[2]), None)

            lbl.bind(texture_size=_sync)
            _sync(None, None)

            with pill.canvas.before:
                Color(1, 0.976, 0.953, 1)
                pill.bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(999)])
                Color(1, 0.894, 0.776, 1)
                pill.bd = Line(rounded_rectangle=[pill.x, pill.y, pill.width, pill.height, dp(999)], width=1)
            pill.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
            pill.bind(size=lambda i, v: setattr(i.bg, 'size', v))
            pill.bind(pos=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))
            pill.bind(size=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(999)]))
            return pill

        if sharing_disp:
            reactions.add_widget(_pill(f"👍 {sharing_disp}"))
            pill_count += 1

        max_occ = (prop or {}).get('max_occupancy')
        if max_occ not in (None, ''):
            reactions.add_widget(_pill(f"❤️ {max_occ} max"))
            pill_count += 1

        if pill_count:
            reactions.add_widget(Widget())
            body.add_widget(reactions)

        card.add_widget(body)

        # Final height based on content
        card.height = (
            card.padding[1]
            + header.height
            + card.spacing
            + media.height
            + card.spacing
            + title_row.height
            + dp(6)
            + (dp(66) if desc else 0)
            + dp(16)
            + (reactions.height if max_occ not in (None, '') or sharing_disp else 0)
            + card.padding[3]
        )

        def _open(_):
            det = self.manager.get_screen('property_detail')
            det.load_property((prop or {}).get('id'))
            self.manager.current = 'property_detail'

        card.bind(on_release=_open)
        fade_in_widget(card, delay=index * 0.05)
        return card
    
    def load_for_uni(self, uni_id, uni_name=None):
        """Load properties for a specific university (student accommodation)"""
        self.uni_id = uni_id
        self.uni_name = uni_name or 'Properties'
        self.filter_city = None
        self.property_type = None
        self.current_filters = {}
        if hasattr(self.ids, 'props_heading'):
            self.ids.props_heading.text = f"Properties for {self.uni_name}"
        self.apply_filters()
    
    def load_for_city(self, city_id, city_name=None):
        """Load long-term properties for a specific city"""
        self.filter_city_id = city_id
        self.filter_city = city_name or ''
        self.property_type = 'long_term'
        self.uni_id = None
        self.current_filters = {}
        if hasattr(self.ids, 'props_heading'):
            self.ids.props_heading.text = f"Long-term Properties in {self.filter_city}" if self.filter_city else "Long-term Properties"
        self.apply_filters_longterm()
    
    def apply_filters_longterm(self):
        """Load long-term properties with city filter"""
        if hasattr(self.ids, 'props_container'):
            self.ids.props_container.clear_widgets()
        if hasattr(self.ids, 'props_loading'):
            self.ids.props_loading.text = 'Loading...'
            start_pulse(self.ids.props_loading)
        
        # Build URL for long-term properties
        url = f"{API_BASE}properties/?property_type=long_term"

        if self.filter_city_id:
            url += f"&city_id={self.filter_city_id}"
        
        # Add filter parameters
        if self.current_filters.get('min_price'):
            url += f"&min_price={self.current_filters['min_price']}"
        if self.current_filters.get('max_price'):
            url += f"&max_price={self.current_filters['max_price']}"
        if self.current_filters.get('order'):
            url += f"&order={self.current_filters['order']}"
        
        cached_request(url, on_success=self.on_loaded_longterm, on_failure=self.on_error)
    
    def apply_filters(self):
        """Load properties with current filters"""
        if hasattr(self.ids, 'props_container'):
            self.ids.props_container.clear_widgets()
        if hasattr(self.ids, 'props_loading'):
            self.ids.props_loading.text = 'Loading...'
            start_pulse(self.ids.props_loading)
        
        # Build URL with filter parameters
        url = f"{API_BASE}universities/{self.uni_id}/properties/?"
        
        # Add filter parameters
        if self.current_filters.get('gender'):
            url += f"&gender={self.current_filters['gender']}"
        if self.current_filters.get('sharing'):
            url += f"&sharing={self.current_filters['sharing']}"
        if self.current_filters.get('overnight'):
            url += f"&overnight=1"
        if self.current_filters.get('min_price'):
            url += f"&min_price={self.current_filters['min_price']}"
        if self.current_filters.get('max_price'):
            url += f"&max_price={self.current_filters['max_price']}"
        if self.current_filters.get('order'):
            url += f"&order={self.current_filters['order']}"
        
        cached_request(url, on_success=self.on_loaded, on_failure=self.on_error)
    
    def set_filter(self, filter_type, value):
        """Set a filter value and reload"""
        self.current_filters[filter_type] = value
        self.apply_filters()
    
    def clear_filters(self):
        """Clear all filters and reload"""
        self.current_filters = {}
        self.apply_filters()

    def on_loaded(self, req, result):
        if hasattr(self.ids, 'props_loading'):
            self.ids.props_loading.text = ''
            stop_pulse(self.ids.props_loading)
        if not hasattr(self.ids, 'props_container'):
            return
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
            card = self._create_web_like_property_card(p, index=idx)
            self.ids.props_container.add_widget(card)
    
    def on_loaded_longterm(self, req, result):
        """Handle loading long-term properties with city filtering"""
        if hasattr(self.ids, 'props_loading'):
            self.ids.props_loading.text = ''
            stop_pulse(self.ids.props_loading)
        if not hasattr(self.ids, 'props_container'):
            return
        self.ids.props_container.clear_widgets()
        
        # Validate result
        if isinstance(result, dict):
            result = result.get('results', [])
        elif not isinstance(result, list):
            empty_label = Label(text=f'Error loading properties: {str(result)[:100]}', color=(0.8, 0.3, 0.3, 1))
            self.ids.props_container.add_widget(empty_label)
            return
        
        if not result:
            suffix = f" in {self.filter_city}" if self.filter_city else ""
            empty_label = Label(text=f'No properties found{suffix}', color=(0.5, 0.5, 0.5, 1))
            self.ids.props_container.add_widget(empty_label)
            return
        
        for idx, p in enumerate(result):
            card = self._create_web_like_property_card(p, index=idx)
            self.ids.props_container.add_widget(card)
            fade_in_widget(card, delay=idx * 0.05)

    def on_error(self, req, error):
        if hasattr(self.ids, 'props_loading'):
            self.ids.props_loading.text = ''
            stop_pulse(self.ids.props_loading)
        if hasattr(self.ids, 'props_container'):
            self.ids.props_container.clear_widgets()
            self.ids.props_container.add_widget(Label(text='Failed to load properties'))
        else:
            print('PropertyListScreen: falling back to simple message')
            bl = BoxLayout(orientation='vertical', padding=12, spacing=8)
            bl.add_widget(Label(text='Failed to load properties (offline fallback)'))
            btn = Button(text='Back to Home', size_hint_y=None, height=40)
            btn.bind(on_release=lambda *_: setattr(self.manager, 'current', 'home'))
            bl.add_widget(btn)
            self.clear_widgets()
            self.add_widget(bl)


class PropertyDetailScreen(Screen):
    current_property = None
    _map_lat = None
    _map_lng = None
    _map_query = None
    _reviews_expanded = False
    _review_rating = 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.viewed_store = JsonStore('viewed_properties.json')
        self._reviews_expanded = False
        self._review_rating = 5

    def show_options_menu(self):
        """Show the global options menu (same as Home)."""
        try:
            home = self.manager.get_screen('home')
            home.show_options_menu()
        except Exception as e:
            print('Failed to open options menu:', e)
    
    def load_property(self, prop_id):
        self.current_property = None
        self._reviews_expanded = False
        if hasattr(self.ids, 'prop_loading'):
            self.ids.prop_loading.text = 'Loading...'
        url = f"{API_BASE}properties/{prop_id}/"
        cached_request(url, on_success=self.on_loaded, on_failure=self.on_error)

    def on_loaded(self, req, result):
        self.current_property = result
        if hasattr(self.ids, 'prop_loading'):
            self.ids.prop_loading.text = ''
        if hasattr(self.ids, 'prop_title'):
            self.ids.prop_title.text = result.get('title', 'Property')
        if hasattr(self.ids, 'prop_desc'):
            self.ids.prop_desc.text = result.get('description', '')

        # Web-like header fields
        self._populate_header_fields(result)

        self._populate_meta(result)
        self._populate_price_badges(result)
        self._populate_map_info(result)
        
        # Load images
        imgs = result.get('images') or []
        self._populate_gallery(imgs)
        self._populate_amenities(result)
        
        # Load reviews
        self.load_reviews()

        # Reset review form state
        self._sync_review_form_state()

        # Track viewed activity
        prop_id = result.get('id')
        if prop_id is not None:
            self.viewed_store.put(str(prop_id), viewed=datetime.now().isoformat(), prop=result)

    def on_error(self, req, error):
        if hasattr(self.ids, 'prop_loading'):
            self.ids.prop_loading.text = ''
        if hasattr(self.ids, 'prop_title'):
            self.ids.prop_title.text = 'Failed to load'
        if hasattr(self.ids, 'prop_desc'):
            self.ids.prop_desc.text = ''

    def _add_meta_row(self, container, text):
        lbl = Label(
            text=text,
            color=(0.35, 0.35, 0.35, 1),
            font_size=sp(13),
            size_hint_y=None,
            height=dp(18),
            halign='left',
            valign='middle'
        )
        lbl.bind(size=lbl.setter('text_size'))
        container.add_widget(lbl)

    def _populate_header_fields(self, result):
        """Populate web-like subtitle (location/university + distance) and the prominent price line."""
        location = result.get('location') or result.get('address')
        university = result.get('university_name') or result.get('university')
        distance = result.get('distance_km') or result.get('distance_to_campus_km')

        parts = []
        if location:
            parts.append(str(location))
        elif university:
            parts.append(str(university))
        else:
            parts.append('Accommodation')

        if distance:
            try:
                parts.append(f"{round(float(distance), 1)} km to campus")
            except Exception:
                parts.append(f"{distance} km to campus")

        if hasattr(self.ids, 'prop_subtitle'):
            self.ids.prop_subtitle.text = " · ".join([p for p in parts if p])

        ptype = result.get('property_type')
        monthly = result.get('price_per_month')
        nightly = result.get('nightly_price')
        overnight = result.get('overnight')

        price_text = ''
        if monthly not in (None, ''):
            price_text = f"[b]${monthly}[/b] [color=#6c757d]/ month[/color]"
        elif overnight and nightly not in (None, ''):
            price_text = f"[b]${nightly}[/b] [color=#6c757d]/ night[/color]"
        else:
            price_text = "[color=#6c757d]Price not available[/color]"

        if hasattr(self.ids, 'prop_price_line'):
            self.ids.prop_price_line.text = price_text

    def _populate_meta(self, result):
        ptype = result.get('property_type')
        is_monthly = ptype in ('long_term', 'shop')
        monthly = result.get('price_per_month')
        nightly = result.get('nightly_price')

        bedrooms = result.get('bedrooms')
        gender = result.get('gender_display') or result.get('gender')
        sharing = result.get('sharing_display') or result.get('sharing')
        overnight = result.get('overnight')
        square_meters = result.get('square_meters')

        # New UI: meta list
        if hasattr(self.ids, 'prop_meta_items'):
            container = self.ids.prop_meta_items
            container.clear_widgets()

            # Match web detail: "Gender · Sharing · Overnight available · Bedrooms · m²"
            summary_parts = []
            if gender:
                summary_parts.append(str(gender))
            if sharing not in (None, ''):
                summary_parts.append(str(sharing))
            if overnight:
                summary_parts.append('Overnight available')
            if bedrooms not in (None, ''):
                summary_parts.append(f"{bedrooms} Bedroom" + ("s" if str(bedrooms) != '1' else ""))
            if square_meters not in (None, ''):
                summary_parts.append(f"{square_meters} m²")
            if summary_parts:
                self._add_meta_row(container, " · ".join(summary_parts))

        # Old UI compatibility: single meta label
        if hasattr(self.ids, 'prop_meta'):
            if is_monthly:
                price = monthly if monthly is not None else 'N/A'
                meta_text = f"Price: ${price} per month"
            else:
                price = nightly if nightly is not None else 'N/A'
                meta_text = f"Price: ${price} per night"
            if distance:
                try:
                    meta_text += f" • {round(float(distance), 1)} km from university"
                except Exception:
                    meta_text += f" • {distance} km from university"
            self.ids.prop_meta.text = meta_text

    def _populate_price_badges(self, result):
        # Prefer the web-like prominent price label if present.
        if hasattr(self.ids, 'prop_price_line'):
            return

        if not hasattr(self.ids, 'price_badges'):
            return

        container = self.ids.price_badges
        container.clear_widgets()

        ptype = result.get('property_type')
        is_monthly = ptype in ('long_term', 'shop')
        monthly = result.get('price_per_month')
        nightly = result.get('nightly_price')

        def _badge(text, bg):
            b = Button(
                text=text,
                size_hint=(None, None),
                size=(dp(165), dp(36)),
                background_normal='',
                background_color=bg,
                color=(0, 0, 0, 1),
                font_size=sp(13),
                bold=True,
                disabled=True
            )
            return b

        if is_monthly:
            value = monthly if monthly is not None else 'N/A'
            container.add_widget(_badge(f"Monthly ${value}", (1, 0.92, 0.45, 1)))
        else:
            value = nightly if nightly is not None else 'N/A'
            container.add_widget(_badge(f"Nightly ${value}", (0.76, 0.92, 0.72, 1)))

    def _populate_map_info(self, result):
        lat = result.get('latitude')
        lng = result.get('longitude')
        location = result.get('location') or result.get('address')
        city = result.get('city_name') or result.get('city')
        university = result.get('university_name') or result.get('university')

        # Payment/visibility hints (web uses has_paid to control "Limited")
        has_paid = result.get('has_paid')
        if has_paid is None:
            has_paid = result.get('admin_fee_paid')
        if has_paid is None:
            has_paid = result.get('has_paid_admin_fee')

        self._map_lat = lat
        self._map_lng = lng
        self._map_query = location or city or university

        # Web-style "Limited" badge when precise location isn't available.
        if isinstance(has_paid, bool):
            limited = not has_paid
        else:
            limited = (lat is None or lng is None) and not location

        if hasattr(self.ids, 'map_limited_badge'):
            self.ids.map_limited_badge.opacity = 1 if limited else 0
        if hasattr(self.ids, 'map_limited_badge_desktop'):
            self.ids.map_limited_badge_desktop.opacity = 1 if limited else 0

        # Embedded map preview (static image) to match the web's map block.
        map_url = ''
        if lat is not None and lng is not None:
            try:
                map_url = (
                    'https://staticmap.openstreetmap.de/staticmap.php'
                    f'?center={lat},{lng}&zoom=15&size=800x400&markers={lat},{lng},red-pushpin'
                )
            except Exception:
                map_url = ''

        for img_id in ('map_image', 'map_image_desktop'):
            if hasattr(self.ids, img_id):
                self.ids[img_id].source = map_url
                try:
                    self.ids[img_id].reload()
                except Exception:
                    pass

        placeholder_text = '' if map_url else 'Map preview unavailable'
        for ph_id in ('map_placeholder', 'map_placeholder_desktop'):
            if hasattr(self.ids, ph_id):
                self.ids[ph_id].text = placeholder_text

        # Match web wording closely
        text_value = str(location) if location else 'Location available after admin fee payment'
        if hasattr(self.ids, 'map_info'):
            self.ids.map_info.text = text_value
        if hasattr(self.ids, 'map_info_desktop'):
            self.ids.map_info_desktop.text = text_value

    def _populate_gallery(self, imgs):
        if not hasattr(self.ids, 'gallery_container'):
            return
        container = self.ids.gallery_container
        container.clear_widgets()

        if not imgs:
            empty = Label(
                text='No images available.',
                color=(0.45, 0.45, 0.45, 1),
                font_size=sp(13),
                size_hint=(None, 1),
                width=dp(240),
                halign='left',
                valign='middle'
            )
            empty.bind(size=empty.setter('text_size'))
            container.add_widget(empty)
            return

        from kivy.uix.behaviors import ButtonBehavior

        class ImageThumb(ButtonBehavior, BoxLayout):
            pass

        for item in imgs[:12]:
            url = item.get('image') or item.get('url')
            if not url:
                continue

            # Web thumb size: 120 x 180
            thumb = ImageThumb(orientation='vertical', size_hint=(None, None), size=(dp(120), dp(180)))
            from kivy.graphics import Color, RoundedRectangle
            with thumb.canvas.before:
                Color(0.94, 0.94, 0.94, 1)
                thumb.bg = RoundedRectangle(pos=thumb.pos, size=thumb.size, radius=[dp(10)])
            thumb.bind(pos=lambda w, v: setattr(w.bg, 'pos', v))
            thumb.bind(size=lambda w, v: setattr(w.bg, 'size', v))

            img = AsyncImage(source=url, fit_mode='contain')
            thumb.add_widget(img)
            thumb.bind(on_release=lambda _w, u=url: self.open_image_modal(u))
            container.add_widget(thumb)

    def _normalize_amenities(self, amenities):
        if not amenities:
            return []
        if isinstance(amenities, list):
            return [str(a).strip() for a in amenities if str(a).strip()]
        if isinstance(amenities, str):
            raw = amenities.replace('\n', ',')
            return [p.strip() for p in raw.split(',') if p.strip()]
        return [str(amenities).strip()]

    def _populate_amenities(self, result):
        if not hasattr(self.ids, 'amenities_container'):
            return
        container = self.ids.amenities_container
        container.clear_widgets()

        amenities = self._normalize_amenities(result.get('amenities'))
        if not amenities:
            container.add_widget(Label(
                text='No amenities listed.',
                color=(0.45, 0.45, 0.45, 1),
                font_size=sp(13),
                size_hint_y=None,
                height=dp(22),
                halign='left',
                valign='middle'
            ))
            return

        from kivy.uix.gridlayout import GridLayout
        from kivy.graphics import Color, RoundedRectangle, Line

        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        def _pill(text):
            pill = Label(
                text=str(text),
                font_size=sp(12),
                color=(0.2, 0.2, 0.2, 1),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(28),
            )
            pill.bind(size=pill.setter('text_size'))
            with pill.canvas.before:
                Color(0.97, 0.97, 0.97, 1)
                pill.bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(10)])
                Color(0.91, 0.91, 0.91, 1)
                pill.bd = Line(rounded_rectangle=[pill.x, pill.y, pill.width, pill.height, dp(10)], width=1)
            pill.bind(pos=lambda i, _v: (setattr(i.bg, 'pos', i.pos), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(10)])))
            pill.bind(size=lambda i, _v: (setattr(i.bg, 'size', i.size), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(10)])))
            return pill

        for a in amenities[:20]:
            grid.add_widget(_pill(a))

        container.add_widget(grid)

    def open_maps(self):
        try:
            import urllib.parse
            import webbrowser

            if self._map_lat is not None and self._map_lng is not None:
                q = f"{self._map_lat},{self._map_lng}"
            else:
                q = self._map_query or ''
            if not q:
                return
            url = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(str(q))
            webbrowser.open(url)
        except Exception as e:
            print('Failed to open maps:', e)

    def open_image_modal(self, image_url: str):
        try:
            from kivy.uix.popup import Popup
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            content.add_widget(AsyncImage(source=image_url, fit_mode='contain'))
            btn = Button(text='Close', size_hint_y=None, height=dp(44), background_normal='', background_color=(0.86, 0.86, 0.86, 1), color=(0.15, 0.15, 0.15, 1))
            content.add_widget(btn)
            popup = Popup(title='', content=content, size_hint=(0.92, 0.92))
            btn.bind(on_release=lambda *_: popup.dismiss())
            popup.open()
        except Exception as e:
            print('Failed to open image modal:', e)
    
    def load_reviews(self):
        """Load reviews for the current property"""
        if not self.current_property:
            return
        
        reviews = self.current_property.get('reviews', []) or []
        if not hasattr(self.ids, 'reviews_container'):
            return

        container = self.ids.reviews_container
        container.clear_widgets()

        total_reviews = len(reviews)
        avg_rating = self.current_property.get('average_rating')

        # Header rating summary (web-style)
        if hasattr(self.ids, 'rating_summary') and hasattr(self.ids, 'reviews_star_row') and hasattr(self.ids, 'reviews_avg_score') and hasattr(self.ids, 'reviews_count'):
            if total_reviews > 0 and avg_rating is not None:
                self.ids.rating_summary.opacity = 1
                self.ids.reviews_avg_score.text = f"{float(avg_rating):.1f}"
                self.ids.reviews_count.text = f"{total_reviews} review" + ("s" if total_reviews != 1 else "")

                stars_row = self.ids.reviews_star_row
                stars_row.clear_widgets()
                try:
                    filled = int(round(float(avg_rating)))
                except Exception:
                    filled = 0
                filled = max(0, min(5, filled))
                for i in range(1, 6):
                    stars_row.add_widget(Label(
                        text='★' if i <= filled else '☆',
                        font_size=sp(16),
                        color=(0.96, 0.75, 0.04, 1),
                        size_hint_x=None,
                        width=dp(14),
                        halign='center',
                        valign='middle',
                    ))
            else:
                self.ids.rating_summary.opacity = 0

        if total_reviews == 0:
            container.add_widget(Label(
                text='No reviews yet.',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(34),
                halign='left',
                valign='middle'
            ))
            self._sync_reviews_toggle(total_reviews)
            return

        # Render reviews (web shows first 5 + show more)
        limit = total_reviews if self._reviews_expanded else 5
        for review in reviews[:limit]:
            container.add_widget(self.create_review_widget(review))

        self._sync_reviews_toggle(total_reviews)
    
    def create_review_widget(self, review):
        """Create a widget for displaying a review"""
        # Web-like review card: avatar + name + stars + date, then comment.
        box = BoxLayout(orientation='vertical', padding=[0, dp(10)], spacing=dp(8), size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        from kivy.graphics import Color, Line, RoundedRectangle
        with box.canvas.before:
            Color(0, 0, 0, 0.08)
            box.top_line = Line(points=[0, 0, 0, 0], width=1)

        def _sync_line(_inst, _val):
            # top border line
            box.top_line.points = [box.x, box.top, box.right, box.top]

        box.bind(pos=_sync_line, size=_sync_line)

        head = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(44))

        # Avatar
        avatar = Label(text='A', size_hint=(None, None), size=(dp(40), dp(40)), bold=True, color=(0.12, 0.25, 0.68, 1), halign='center', valign='middle')
        avatar.bind(size=avatar.setter('text_size'))
        with avatar.canvas.before:
            Color(0.93, 0.95, 1, 1)
            avatar.bg = RoundedRectangle(pos=avatar.pos, size=avatar.size, radius=[dp(20)])
        avatar.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
        avatar.bind(size=lambda i, v: setattr(i.bg, 'size', v))

        username = (review or {}).get('user_username') or ''
        email = (review or {}).get('user_email') or ''
        name = username or email or 'User'
        initial = (name[:1] or 'U').upper()
        avatar.text = initial

        head.add_widget(avatar)

        meta = BoxLayout(orientation='vertical', spacing=dp(2))
        name_lbl = Label(text=str(name)[:30], bold=True, color=(0.13, 0.13, 0.13, 1), halign='left', valign='middle', size_hint_y=None, height=dp(18))
        name_lbl.bind(size=name_lbl.setter('text_size'))
        meta.add_widget(name_lbl)

        stars_row = BoxLayout(orientation='horizontal', spacing=dp(2), size_hint_y=None, height=dp(18))
        rating = int((review or {}).get('rating') or 0)
        rating = max(0, min(5, rating))
        for i in range(1, 6):
            stars_row.add_widget(Label(
                text='★' if i <= rating else '☆',
                font_size=sp(14),
                color=(0.96, 0.75, 0.04, 1),
                size_hint_x=None,
                width=dp(12),
            ))

        # Date
        created_at = (review or {}).get('created_at') or ''
        date_lbl = Label(text=str(created_at)[:10], font_size=sp(12), color=(0.45, 0.45, 0.45, 1), halign='left', valign='middle')
        date_lbl.bind(size=date_lbl.setter('text_size'))

        stars_and_date = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(18))
        stars_and_date.add_widget(stars_row)
        stars_and_date.add_widget(date_lbl)

        meta.add_widget(stars_and_date)
        head.add_widget(meta)

        box.add_widget(head)

        comment = Label(
            text=str((review or {}).get('comment') or ''),
            font_size=sp(12),
            color=(0.45, 0.45, 0.45, 1),
            halign='left',
            valign='top',
            size_hint_y=None,
        )
        comment.bind(size=comment.setter('text_size'))
        comment.bind(texture_size=lambda i, v: setattr(i, 'height', v[1] + dp(6)))
        box.add_widget(comment)

        return box

    def _sync_reviews_toggle(self, total_reviews: int):
        if not hasattr(self.ids, 'reviews_toggle'):
            return
        if total_reviews > 5:
            self.ids.reviews_toggle.opacity = 1
            self.ids.reviews_toggle.disabled = False
            self.ids.reviews_toggle.text = 'Show less' if self._reviews_expanded else 'Show more'
        else:
            self.ids.reviews_toggle.opacity = 0
            self.ids.reviews_toggle.disabled = True

    def toggle_reviews(self):
        self._reviews_expanded = not self._reviews_expanded
        self.load_reviews()

    def _is_authenticated(self):
        return bool(getattr(self.manager, 'token', None))

    def _sync_review_form_state(self):
        if not hasattr(self.ids, 'review_form'):
            return
        authed = self._is_authenticated()

        # Show a web-like hint.
        if hasattr(self.ids, 'review_form_title'):
            self.ids.review_form_title.text = '' if authed else 'Login to write a review.'

        self.ids.review_form.opacity = 1 if authed else 0
        self.ids.review_form.disabled = False if authed else True

        if authed and hasattr(self.ids, 'review_status'):
            self.ids.review_status.text = ''

        self.set_review_rating(self._review_rating)

    def set_review_rating(self, value: int):
        try:
            v = int(value)
        except Exception:
            v = 5
        v = max(1, min(5, v))
        self._review_rating = v

        # Update star buttons
        for i in range(1, 6):
            star_id = f'star_{i}'
            if hasattr(self.ids, star_id):
                self.ids[star_id].text = '★' if i <= v else '☆'
        if hasattr(self.ids, 'review_rating_hint'):
            self.ids.review_rating_hint.text = f"{v} star" + ("s" if v != 1 else "")

    def submit_review(self):
        if not self.current_property:
            return
        if not self._is_authenticated():
            if hasattr(self.ids, 'review_status'):
                self.ids.review_status.text = 'Please login to submit a review.'
            return

        prop_id = self.current_property.get('id')
        if not prop_id:
            return

        if not hasattr(self.ids, 'review_comment'):
            return
        comment = (self.ids.review_comment.text or '').strip()
        if not comment:
            if hasattr(self.ids, 'review_status'):
                self.ids.review_status.text = 'Please write a review.'
            return

        if hasattr(self.ids, 'review_status'):
            self.ids.review_status.text = 'Submitting...'

        import json
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = f'Bearer {self.manager.token}'
        body = json.dumps({'rating': int(self._review_rating), 'comment': comment})

        def on_success(_req, _res):
            if hasattr(self.ids, 'review_status'):
                self.ids.review_status.text = 'Submitted.'
            if hasattr(self.ids, 'review_comment'):
                self.ids.review_comment.text = ''
            # Refresh property details to include new review
            self.load_property(prop_id)

        def on_error(_req, error):
            msg = 'Failed to submit review.'
            try:
                # When user already reviewed, API returns ValidationError detail.
                if isinstance(error, dict):
                    msg = error.get('detail') or msg
            except Exception:
                pass
            if hasattr(self.ids, 'review_status'):
                self.ids.review_status.text = msg

        UrlRequest(
            f"{API_BASE}properties/{prop_id}/reviews/",
            on_success=on_success,
            on_error=on_error,
            on_failure=on_error,
            req_body=body,
            req_headers=headers,
            method='POST',
        )
    
    def contact_landlord(self):
        """Handle contact landlord button press"""
        if not self.current_property:
            return
        
        prop_id = self.current_property.get('id')
        if not prop_id:
            return
        
        # Navigate to contact screen
        if hasattr(self.manager, 'get_screen'):
            contact_screen = self.manager.get_screen('property_contact')
            contact_screen.load_contact_info(prop_id, self.current_property)
            self.manager.current = 'property_contact'


class PropertyContactScreen(Screen):
    current_property = None
    
    def load_contact_info(self, prop_id, prop_data):
        """Load contact information and payment status"""
        self.current_property = prop_data
        self.property_id = prop_id
        
        if hasattr(self.ids, 'contact_property_name'):
            self.ids.contact_property_name.text = str(prop_data.get('title', ''))
        
        # Try to get contact info
        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'students': 1})  # Default to 1 student
        
        UrlRequest(
            f"{API_BASE}properties/{prop_id}/contact/",
            on_success=self.on_contact_success,
            on_error=self.on_contact_error,
            on_failure=self.on_contact_error,
            req_body=data,
            req_headers=headers,
            method='POST'
        )

    def _panel(self, bg_rgba, radius_dp=12, border_rgba=None, border_width=1, left_bar_rgba=None):
        panel = BoxLayout(
            orientation='vertical',
            padding=[dp(14), dp(12)],
            spacing=dp(10),
            size_hint_y=None,
        )
        panel.bind(minimum_height=panel.setter('height'))

        from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
        with panel.canvas.before:
            Color(*bg_rgba)
            panel._bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(radius_dp)])
            if left_bar_rgba is not None:
                Color(*left_bar_rgba)
                panel._left = Rectangle(pos=(panel.x, panel.y), size=(dp(4), panel.height))
            if border_rgba is not None:
                Color(*border_rgba)
                panel._border = Line(width=border_width, rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, dp(radius_dp)))

        def _sync(_inst, _val):
            panel._bg.pos = panel.pos
            panel._bg.size = panel.size
            if hasattr(panel, '_border'):
                panel._border.rounded_rectangle = (panel.x, panel.y, panel.width, panel.height, dp(radius_dp))
            if hasattr(panel, '_left'):
                panel._left.pos = (panel.x, panel.y)
                panel._left.size = (dp(4), panel.height)

        panel.bind(pos=_sync, size=_sync)
        return panel

    def _contact_detail_row(self, icon_text, label_text, value_text):
        row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None)
        row.bind(minimum_height=row.setter('height'))

        from kivy.graphics import Color, RoundedRectangle, Line
        with row.canvas.before:
            Color(1, 1, 1, 1)
            row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(10)])
            Color(0, 0, 0, 0.08)
            row._border = Line(width=1, rounded_rectangle=(row.x, row.y, row.width, row.height, dp(10)))

        def _sync(_inst, _val):
            row._bg.pos = row.pos
            row._bg.size = row.size
            row._border.rounded_rectangle = (row.x, row.y, row.width, row.height, dp(10))

        row.bind(pos=_sync, size=_sync)

        icon = Label(text=icon_text, font_size=sp(26), size_hint=(None, None), size=(dp(34), dp(34)), color=(0.13, 0.13, 0.13, 1), halign='center', valign='middle')
        icon.bind(size=icon.setter('text_size'))
        row.add_widget(icon)

        info = BoxLayout(orientation='vertical', spacing=dp(2))
        lbl = Label(text=str(label_text).upper(), font_size=sp(11), color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=dp(14), halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        val = Label(text=str(value_text) if value_text else 'Not provided', bold=True, font_size=sp(15), color=(0.13, 0.13, 0.13, 1), size_hint_y=None, height=dp(20), halign='left', valign='middle')
        val.bind(size=val.setter('text_size'))
        info.add_widget(lbl)
        info.add_widget(val)
        row.add_widget(info)

        row.height = dp(56)
        row.padding = [dp(12), dp(10)]
        return row

    def _static_map_url(self, lat, lng):
        if lat is None or lng is None:
            return ''
        try:
            return (
                'https://staticmap.openstreetmap.de/staticmap.php'
                f'?center={lat},{lng}&zoom=15&size=800x400&markers={lat},{lng},red-pushpin'
            )
        except Exception:
            return ''
    
    def on_contact_success(self, req, result):
        """Handle successful contact retrieval"""
        if hasattr(self.ids, 'contact_container'):
            container = self.ids.contact_container
            container.clear_widgets()
            
            # Check if we have contact details
            if result.get('house_number'):
                # User has paid - show contact details
                self.show_contact_details(container, result)
            else:
                # User needs to pay
                self.show_payment_form(container, result)
    
    def on_contact_error(self, req, error):
        """Handle contact retrieval error"""
        # 402 means payment required
        if hasattr(req, 'resp_status') and req.resp_status == 402:
            # Parse the response to get payment instructions
            import json
            try:
                result = json.loads(req.result)
                if hasattr(self.ids, 'contact_container'):
                    self.show_payment_form(self.ids.contact_container, result)
            except:
                pass
        # 403 means user has an approved payment but has exhausted uses
        elif hasattr(req, 'resp_status') and req.resp_status == 403:
            if hasattr(self.ids, 'contact_container'):
                container = self.ids.contact_container
                container.clear_widgets()

                detail = None
                try:
                    if isinstance(error, dict):
                        detail = error.get('detail')
                except Exception:
                    detail = None
                if not detail:
                    try:
                        import json
                        parsed = json.loads(req.result)
                        if isinstance(parsed, dict):
                            detail = parsed.get('detail')
                    except Exception:
                        detail = None
                if not detail:
                    detail = 'No remaining uses on your approved payment. Please pay again.'

                warn = self._panel(bg_rgba=(1, 0.95, 0.82, 1), radius_dp=12, left_bar_rgba=(1, 0.76, 0.15, 1))
                warn_title = Label(
                    text='⚠️ Views exhausted',
                    bold=True,
                    font_size=sp(13),
                    color=(0.52, 0.36, 0.0, 1),
                    halign='left',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(18),
                )
                warn_title.bind(size=warn_title.setter('text_size'))
                warn.add_widget(warn_title)

                warn_msg = Label(
                    text=str(detail),
                    font_size=sp(12),
                    color=(0.52, 0.36, 0.0, 1),
                    halign='left',
                    valign='top',
                    size_hint_y=None,
                )
                warn_msg.bind(size=warn_msg.setter('text_size'))
                warn_msg.bind(texture_size=lambda i, v: setattr(i, 'height', v[1] + dp(6)))
                warn.add_widget(warn_msg)

                container.add_widget(warn)

                # Show the payment form so the user can pay again to unlock more views.
                self.show_payment_form(container, {}, clear=False)
        else:
            if hasattr(self.ids, 'contact_container'):
                container = self.ids.contact_container
                container.clear_widgets()
                alert = self._panel(bg_rgba=(1, 0.95, 0.95, 1), radius_dp=12, left_bar_rgba=(0.86, 0.15, 0.15, 1))
                msg = Label(
                    text='Please login to view contact details',
                    color=(0.45, 0.1, 0.1, 1),
                    font_size=sp(13),
                    bold=True,
                    halign='left',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(18),
                )
                msg.bind(size=msg.setter('text_size'))
                alert.add_widget(msg)
                container.add_widget(alert)
    
    def show_contact_details(self, container, data):
        """Display landlord contact details"""
        container.clear_widgets()

        # Web-like approved info box
        approved = self._panel(bg_rgba=(0.83, 0.93, 0.85, 1), radius_dp=12, left_bar_rgba=(0.16, 0.65, 0.31, 1))
        approved.add_widget(Label(
            text='✓ Admin fee payment approved',
            color=(0.08, 0.35, 0.18, 1),
            bold=True,
            font_size=sp(13),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(18),
        ))
        container.add_widget(approved)

        # Contact detail rows
        phone = data.get('contact_phone')
        house = data.get('house_number')
        caretaker = data.get('caretaker_number')
        lat = data.get('latitude')
        lng = data.get('longitude')
        address = None
        try:
            address = (self.current_property or {}).get('location') or (self.current_property or {}).get('address')
        except Exception:
            address = None

        container.add_widget(self._contact_detail_row('📱', 'Phone Number', phone))
        container.add_widget(self._contact_detail_row('🏠', 'House Number', house))
        container.add_widget(self._contact_detail_row('👤', 'Caretaker', caretaker))
        if address:
            container.add_widget(self._contact_detail_row('📍', 'Full Address', address))
        if lat is not None and lng is not None:
            container.add_widget(self._contact_detail_row('🗺️', 'Coordinates', f"{lat}, {lng}"))

            # Map preview block (web has embedded map)
            map_wrap = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(240))
            from kivy.graphics import Color, RoundedRectangle
            with map_wrap.canvas.before:
                Color(0.91, 0.91, 0.91, 1)
                map_wrap._bg = RoundedRectangle(pos=map_wrap.pos, size=map_wrap.size, radius=[dp(12)])
            map_wrap.bind(pos=lambda w, v: setattr(w._bg, 'pos', v))
            map_wrap.bind(size=lambda w, v: setattr(w._bg, 'size', v))

            map_img = AsyncImage(source=self._static_map_url(lat, lng), allow_stretch=True, keep_ratio=False)
            map_wrap.add_widget(map_img)
            container.add_widget(map_wrap)

            open_btn = Button(
                text='Open in Google Maps',
                size_hint_y=None,
                height=dp(36),
                background_normal='',
                background_color=(0, 0, 0, 0),
                color=(0.05, 0.43, 0.99, 1),
                bold=True,
            )
            open_btn.bind(on_release=lambda *_: self.open_maps())
            container.add_widget(open_btn)
    
    def show_payment_form(self, container, data, clear: bool = True):
        """Display payment form"""
        if clear:
            container.clear_widgets()

        pay = self._panel(bg_rgba=(1, 0.95, 0.82, 1), radius_dp=12)

        icon = Label(text='🔒', font_size=sp(46), size_hint_y=None, height=dp(52), halign='center', valign='middle', text_size=(0, 0), color=(0.13, 0.13, 0.13, 1))
        pay.add_widget(icon)

        pay.add_widget(Label(
            text='Payment Required',
            bold=True,
            font_size=sp(18),
            color=(0.13, 0.13, 0.13, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(24),
        ))

        hint = Label(
            text='Pay the admin fee to unlock contact details',
            font_size=sp(13),
            color=(0.35, 0.35, 0.35, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(18),
        )
        hint.bind(size=hint.setter('text_size'))
        pay.add_widget(hint)

        # Students input + calculate (web-like)
        students_row = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(44))
        students_lbl = Label(text='Students', size_hint_x=None, width=dp(80), color=(0.2, 0.2, 0.2, 1), bold=True, halign='left', valign='middle')
        students_lbl.bind(size=students_lbl.setter('text_size'))
        from kivy.uix.textinput import TextInput
        students_input = TextInput(text='1', multiline=False, input_filter='int')
        calc_btn = Button(
            text='Calculate',
            size_hint_x=None,
            width=dp(120),
            background_normal='',
            background_color=(1, 0.84, 0, 1),
            color=(0, 0, 0, 1),
            bold=True,
        )
        calc_btn.bind(on_release=lambda *_: self.recalculate_admin_fee(students_input.text))
        students_row.add_widget(students_lbl)
        students_row.add_widget(students_input)
        students_row.add_widget(calc_btn)
        pay.add_widget(students_row)
        
        # Payment instructions if available
        payment_instructions = data.get('payment_instructions', {})
        if payment_instructions:
            amount = payment_instructions.get('amount', 0)

            amt = Label(
                text=f"${amount}",
                bold=True,
                font_size=sp(24),
                color=(0.13, 0.13, 0.13, 1),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(30),
            )
            pay.add_widget(amt)

            instructions = Label(
                text=str(payment_instructions.get('instructions', '')).strip(),
                font_size=sp(12),
                color=(0.35, 0.35, 0.35, 1),
                halign='left',
                valign='top',
                size_hint_y=None,
            )
            instructions.bind(size=instructions.setter('text_size'))
            instructions.bind(texture_size=lambda i, v: setattr(i, 'height', v[1] + dp(6)))
            pay.add_widget(instructions)

            confirmation_input = TextInput(
                hint_text='Paste your payment confirmation message here...',
                multiline=True,
                size_hint_y=None,
                height=dp(110),
            )
            pay.add_widget(confirmation_input)

            submit_btn = Button(
                text='Submit Payment Confirmation',
                size_hint_y=None,
                height=dp(46),
                background_normal='',
                background_color=(1, 0.84, 0, 1),
                color=(0, 0, 0, 1),
                bold=True,
            )
            submit_btn.bind(on_release=lambda *_: self.submit_payment(confirmation_input.text))
            pay.add_widget(submit_btn)

        container.add_widget(pay)

    def recalculate_admin_fee(self, students_text):
        """Re-request /contact/ with a students count to compute amount (web-like)."""
        if not getattr(self, 'property_id', None):
            return
        try:
            students = int(str(students_text).strip() or '1')
        except Exception:
            students = 1
        if students < 1:
            students = 1

        import json
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({'students': students})

        UrlRequest(
            f"{API_BASE}properties/{self.property_id}/contact/",
            on_success=self.on_contact_success,
            on_error=self.on_contact_error,
            on_failure=self.on_contact_error,
            req_body=body,
            req_headers=headers,
            method='POST',
        )
    
    def submit_payment(self, confirmation_text):
        """Submit payment confirmation"""
        if not confirmation_text.strip():
            return
        
        if not self.current_property:
            return
        
        university_id = self.current_property.get('university', {}).get('id')
        if not university_id:
            return
        
        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'university': university_id,
            'for_number_of_students': 1,
            'confirmation_text': confirmation_text
        })
        
        UrlRequest(
            f"{API_BASE}payments/confirm/",
            on_success=self.on_payment_submitted,
            on_error=self.on_payment_error,
            on_failure=self.on_payment_error,
            req_body=data,
            req_headers=headers,
            method='POST'
        )
    
    def on_payment_submitted(self, req, result):
        """Handle successful payment submission"""
        if hasattr(self.ids, 'contact_container'):
            container = self.ids.contact_container
            container.clear_widgets()

            pending = self._panel(bg_rgba=(1, 0.95, 0.82, 1), radius_dp=12, left_bar_rgba=(1, 0.76, 0.15, 1))
            title = Label(
                text='⏳ Payment Confirmation Status: Pending',
                bold=True,
                font_size=sp(14),
                color=(0.52, 0.36, 0.0, 1),
                halign='left',
                valign='middle',
                size_hint_y=None,
                height=dp(20),
            )
            title.bind(size=title.setter('text_size'))
            pending.add_widget(title)
            msg = Label(
                text='Your payment confirmation has been submitted and is awaiting admin approval. You will be able to view landlord contact details once approved.',
                font_size=sp(12),
                color=(0.52, 0.36, 0.0, 1),
                halign='left',
                valign='top',
                size_hint_y=None,
            )
            msg.bind(size=msg.setter('text_size'))
            msg.bind(texture_size=lambda i, v: setattr(i, 'height', v[1] + dp(6)))
            pending.add_widget(msg)
            container.add_widget(pending)
    
    def on_payment_error(self, req, error):
        """Handle payment submission error"""
        if hasattr(self.ids, 'contact_container'):
            error_label = Label(
                text='Failed to submit payment. Please try again.',
                color=(0.8, 0, 0, 1)
            )
            self.ids.contact_container.add_widget(error_label)


class LoginScreen(Screen):
    def show_options_menu(self):
        """Show the global options menu (same as Home)."""
        try:
            home = self.manager.get_screen('home')
            home.show_options_menu()
        except Exception as e:
            print('Failed to open options menu:', e)

    def do_login(self):
        if not hasattr(self.ids, 'email_input') or not hasattr(self.ids, 'password_input'):
            return
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        if hasattr(self.ids, 'login_status'):
            self.ids.login_status.text = 'Logging in...'
            start_pulse(self.ids.login_status)
        
        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'email': email, 'password': password})
        UrlRequest(API_AUTH_BASE + 'login/', on_success=self.on_login_success, 
                  on_error=self.on_login_error, on_failure=self.on_login_error,
                  req_body=data, req_headers=headers, method='POST')
    
    def on_login_success(self, req, result):
        # Store user session
        session = SessionManager()
        session.set_user(result)

        # Sync app-level auth state for KV bindings
        try:
            app = App.get_running_app()
            if hasattr(app, 'refresh_auth_state'):
                app.refresh_auth_state()
        except Exception:
            pass
        
        if hasattr(self.ids, 'login_status'):
            self.ids.login_status.text = 'Login successful!'
            stop_pulse(self.ids.login_status)
        # Navigate to home
        self.manager.current = 'home'
    
    def on_login_error(self, req, error):
        if hasattr(self.ids, 'login_status'):
            self.ids.login_status.text = 'Login failed. Please check your credentials.'
            stop_pulse(self.ids.login_status)


class RegisterScreen(Screen):
    def show_options_menu(self):
        """Show the global options menu (same as Home)."""
        try:
            home = self.manager.get_screen('home')
            home.show_options_menu()
        except Exception as e:
            print('Failed to open options menu:', e)

    def do_register(self):
        if not all(hasattr(self.ids, attr) for attr in ['email_input', 'password_input', 'confirm_password_input', 'username_input', 'full_name_input', 'phone_input', 'address_input', 'role_input']):
            return
        
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        confirm_password = self.ids.confirm_password_input.text
        username = self.ids.username_input.text
        full_name = self.ids.full_name_input.text
        phone_number = self.ids.phone_input.text
        address = self.ids.address_input.text
        role = (self.ids.role_input.text or 'general').strip() or 'general'
        
        if password != confirm_password:
            if hasattr(self.ids, 'register_status'):
                self.ids.register_status.text = 'Passwords do not match'
            return
        
        if hasattr(self.ids, 'register_status'):
            self.ids.register_status.text = 'Creating account...'
            start_pulse(self.ids.register_status)
        
        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'email': email,
            'password': password,
            'username': username,
            'full_name': full_name,
            'phone_number': phone_number,
            'address': address,
            'role': role
        })
        UrlRequest(API_AUTH_BASE + 'register/', on_success=self.on_register_success,
                  on_error=self.on_register_error, on_failure=self.on_register_error,
                  req_body=data, req_headers=headers, method='POST')
    
    def on_register_success(self, req, result):
        if hasattr(self.ids, 'register_status'):
            self.ids.register_status.text = 'Account created! Please login.'
            stop_pulse(self.ids.register_status)
        # Navigate to login
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'login'), 1.5)
    
    def on_register_error(self, req, error):
        if hasattr(self.ids, 'register_status'):
            self.ids.register_status.text = 'Registration failed. Please try again.'
            stop_pulse(self.ids.register_status)


class ProfileScreen(Screen):
    def on_pre_enter(self):
        """Load user profile data when screen is entered"""
        self.load_profile()

    def _set_label(self, widget_id: str, text: str):
        if hasattr(self.ids, widget_id):
            try:
                self.ids[widget_id].text = text
            except Exception:
                pass

    def _fmt_dt(self, value):
        if not value:
            return ''
        if isinstance(value, str):
            # DRF typically returns ISO strings; keep it readable.
            return value.replace('T', ' ')[:19]
        try:
            return str(value)
        except Exception:
            return ''
    
    def load_profile(self):
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = 'Loading...'
        cached_request(API_AUTH_BASE + 'profile/', on_success=self.on_profile_loaded, on_failure=self.on_profile_error)
    
    def on_profile_loaded(self, req, result):
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = ''
        if hasattr(self.ids, 'email_display'):
            self.ids.email_display.text = result.get('email', '')
        if hasattr(self.ids, 'username_input'):
            self.ids.username_input.text = result.get('username', '') or ''
        if hasattr(self.ids, 'full_name_input'):
            self.ids.full_name_input.text = result.get('full_name', '')
        if hasattr(self.ids, 'phone_input'):
            self.ids.phone_input.text = result.get('phone_number', '') or ''
        if hasattr(self.ids, 'address_input'):
            self.ids.address_input.text = result.get('address', '') or ''
        if hasattr(self.ids, 'role_display'):
            self.ids.role_display.text = f"Role: {result.get('role', 'general')}"

        admin_fee = result.get('admin_fee') or {}
        is_active = bool(admin_fee.get('is_active'))
        uses_remaining = admin_fee.get('uses_remaining', 0)
        valid_until = self._fmt_dt(admin_fee.get('valid_until'))
        university = admin_fee.get('university')

        if is_active:
            uni_text = f" ({university})" if university else ''
            self._set_label('admin_fee_status', f"Active{uni_text}")
            self._set_label('views_remaining_display', f"Remaining accommodations to view: {uses_remaining}")
            self._set_label('valid_until_display', f"Valid until: {valid_until}" if valid_until else '')
        else:
            self._set_label('admin_fee_status', 'Not active')
            self._set_label('views_remaining_display', 'Remaining accommodations to view: 0')
            self._set_label('valid_until_display', '')

        if hasattr(self.ids, 'history_container'):
            container = self.ids.history_container
            try:
                container.clear_widgets()
            except Exception:
                pass

            history = result.get('booking_history') or []
            if not history:
                container.add_widget(Label(
                    text='No history yet',
                    color=(0.5, 0.5, 0.5, 1),
                    size_hint_y=None,
                    height=dp(26),
                    halign='left',
                    valign='middle',
                ))
                return

            for item in history:
                title = (item or {}).get('property_title') or 'Property'
                viewed_at = self._fmt_dt((item or {}).get('viewed_at'))
                uni = (item or {}).get('university')
                meta_parts = []
                if viewed_at:
                    meta_parts.append(viewed_at)
                if uni:
                    meta_parts.append(str(uni))
                meta = ' • '.join(meta_parts)

                row = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(44), spacing=dp(2))
                row.add_widget(Label(
                    text=f"[b]{title}[/b]",
                    markup=True,
                    color=(0.15, 0.15, 0.15, 1),
                    size_hint_y=None,
                    height=dp(22),
                    halign='left',
                    valign='middle',
                ))
                row.add_widget(Label(
                    text=meta,
                    color=(0.45, 0.45, 0.45, 1),
                    size_hint_y=None,
                    height=dp(18),
                    halign='left',
                    valign='middle',
                ))
                container.add_widget(row)
    
    def on_profile_error(self, req, error):
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = 'Failed to load profile. Please login.'
    
    def save_profile(self):
        if not all(hasattr(self.ids, attr) for attr in ['full_name_input', 'username_input', 'phone_input', 'address_input']):
            return

        full_name = self.ids.full_name_input.text
        username = self.ids.username_input.text
        phone_number = self.ids.phone_input.text
        address = self.ids.address_input.text
        
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = 'Saving...'
            start_pulse(self.ids.profile_status)
        
        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({
            'full_name': full_name,
            'username': username,
            'phone_number': phone_number,
            'address': address,
        })
        UrlRequest(API_AUTH_BASE + 'profile/', on_success=self.on_save_success,
                  on_error=self.on_save_error, on_failure=self.on_save_error,
                  req_body=data, req_headers=headers, method='PATCH')

    def on_save_success(self, req, result):
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = 'Profile updated!'
            stop_pulse(self.ids.profile_status)
        Clock.schedule_once(lambda dt: setattr(self.ids.profile_status, 'text', ''), 2.0)

    def on_save_error(self, req, error):
        if hasattr(self.ids, 'profile_status'):
            self.ids.profile_status.text = 'Failed to save profile'
            stop_pulse(self.ids.profile_status)

    def open_change_password(self):
        try:
            self.manager.current = 'change_password'
        except Exception:
            pass

    def open_my_properties(self):
        # Only meaningful for landlords, but safe to open.
        try:
            self.manager.current = 'my_properties'
        except Exception:
            pass


class ChangePasswordScreen(Screen):
    back_screen = 'profile'

    def go_back(self):
        try:
            self.manager.current = self.back_screen
        except Exception:
            self.manager.current = 'profile'

    def submit_change(self):
        if not all(hasattr(self.ids, attr) for attr in ['old_password_input', 'new_password_input', 'confirm_password_input', 'change_password_status']):
            return

        old_pw = self.ids.old_password_input.text
        new_pw = self.ids.new_password_input.text
        confirm_pw = self.ids.confirm_password_input.text

        if not old_pw or not new_pw:
            self.ids.change_password_status.text = 'Please fill in all fields'
            return
        if new_pw != confirm_pw:
            self.ids.change_password_status.text = 'Passwords do not match'
            return

        self.ids.change_password_status.text = 'Updating...'
        start_pulse(self.ids.change_password_status)

        import json
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({'old_password': old_pw, 'new_password': new_pw})

        def on_success(req, result):
            stop_pulse(self.ids.change_password_status)
            self.ids.change_password_status.text = 'Password updated'
            # clear inputs
            self.ids.old_password_input.text = ''
            self.ids.new_password_input.text = ''
            self.ids.confirm_password_input.text = ''

        def on_error(req, error):
            stop_pulse(self.ids.change_password_status)
            self.ids.change_password_status.text = 'Failed to update password'

        UrlRequest(
            API_AUTH_BASE + 'password/change/',
            on_success=on_success,
            on_error=on_error,
            on_failure=on_error,
            req_body=data,
            req_headers=headers,
            method='POST',
        )


class NotificationsScreen(Screen):
    def on_pre_enter(self):
        """Load notifications when screen is entered"""
        self.load_notifications()
        self.mark_all_read()
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if hasattr(self.manager, 'token') and self.manager.token:
            headers['Authorization'] = f'Bearer {self.manager.token}'
        
        UrlRequest(
            API_BASE + 'notifications/',
            method='POST',
            req_body='action=mark_all_read',
            req_headers=headers,
            on_success=self.on_marked_read,
            on_error=self.on_mark_error,
            on_failure=self.on_mark_error
        )
    
    def on_marked_read(self, req, result):
        pass  # Silent success
    
    def on_mark_error(self, req, error):
        print('Failed to mark notifications as read:', error)
    
    def load_notifications(self):
        if hasattr(self.ids, 'notifications_loading'):
            self.ids.notifications_loading.text = 'Loading...'
        cached_request(API_BASE + 'notifications/', on_success=self.on_notifications_loaded, on_failure=self.on_notifications_error)
    
    def on_notifications_loaded(self, req, result):
        if hasattr(self.ids, 'notifications_loading'):
            self.ids.notifications_loading.text = ''
        
        if not hasattr(self.ids, 'notifications_container'):
            return
        
        container = self.ids.notifications_container
        container.clear_widgets()
        
        if not result or len(result) == 0:
            container.add_widget(Label(
                text='No notifications yet',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(60)
            ))
            return
        
        for notif in result:
            notif_box = BoxLayout(
                orientation='vertical',
                padding=[dp(12), dp(10)],
                spacing=dp(4),
                size_hint_y=None,
                height=dp(80)
            )
            
            # Background color based on read status
            bg_color = (0.95, 0.95, 0.95, 1) if notif.get('is_read') else (0.9, 0.95, 1.0, 1)
            from kivy.graphics import Color, RoundedRectangle
            with notif_box.canvas.before:
                Color(*bg_color)
                notif_box.bg_rect = RoundedRectangle(pos=notif_box.pos, size=notif_box.size, radius=[dp(8)])
            notif_box.bind(pos=lambda w, v: setattr(w.bg_rect, 'pos', v))
            notif_box.bind(size=lambda w, v: setattr(w.bg_rect, 'size', v))
            
            title_label = Label(
                text=f"[b]{notif.get('title', 'Notification')}[/b]",
                markup=True,
                color=(0, 0, 0, 1),
                font_size='14sp',
                size_hint_y=None,
                height=dp(20),
                halign='left',
                valign='top'
            )
            title_label.bind(size=title_label.setter('text_size'))
            
            message_label = Label(
                text=notif.get('message', ''),
                color=(0.3, 0.3, 0.3, 1),
                font_size='12sp',
                size_hint_y=None,
                height=dp(40),
                halign='left',
                valign='top'
            )
            message_label.bind(size=message_label.setter('text_size'))
            
            notif_box.add_widget(title_label)
            notif_box.add_widget(message_label)
            container.add_widget(notif_box)
        
        # Add activity-based notifications
        self.add_activity_notifications(container)
    
    def add_activity_notifications(self, container):
        from kivy.storage.jsonstore import JsonStore
        liked_store = JsonStore('liked_properties.json')
        viewed_store = JsonStore('viewed_properties.json')
        
        activity_notifs = []
        
        if len(liked_store):
            activity_notifs.append({
                'title': 'Liked Properties',
                'message': f'You have {len(liked_store)} liked properties. Check them out!',
                'is_read': False
            })
        
        if len(viewed_store):
            activity_notifs.append({
                'title': 'Recently Viewed',
                'message': f'You have viewed {len(viewed_store)} properties. Explore more!',
                'is_read': False
            })
        
        for notif in activity_notifs:
            notif_box = BoxLayout(
                orientation='vertical',
                padding=[dp(12), dp(10)],
                spacing=dp(4),
                size_hint_y=None,
                height=dp(80)
            )
            
            bg_color = (0.95, 0.95, 0.95, 1)
            from kivy.graphics import Color, RoundedRectangle
            with notif_box.canvas.before:
                Color(*bg_color)
                notif_box.bg_rect = RoundedRectangle(pos=notif_box.pos, size=notif_box.size, radius=[dp(8)])
            notif_box.bind(pos=lambda w, v: setattr(w.bg_rect, 'pos', v))
            notif_box.bind(size=lambda w, v: setattr(w.bg_rect, 'size', v))
            
            title_label = Label(
                text=f"[b]{notif['title']}[/b]",
                markup=True,
                color=(0, 0, 0, 1),
                font_size='14sp',
                size_hint_y=None,
                height=dp(20),
                halign='left',
                valign='top'
            )
            title_label.bind(size=title_label.setter('text_size'))
            
            message_label = Label(
                text=notif['message'],
                color=(0.3, 0.3, 0.3, 1),
                font_size='12sp',
                size_hint_y=None,
                height=dp(40),
                halign='left',
                valign='top'
            )
            message_label.bind(size=message_label.setter('text_size'))
            
            notif_box.add_widget(title_label)
            notif_box.add_widget(message_label)
            container.add_widget(notif_box)
    
    def on_notifications_error(self, req, error):
        if hasattr(self.ids, 'notifications_loading'):
            self.ids.notifications_loading.text = 'Failed to load notifications'


class MyPropertiesScreen(Screen):
    def show_options_menu(self):
        """Show the global options menu (same as Home)."""
        try:
            home = self.manager.get_screen('home')
            home.show_options_menu()
        except Exception as e:
            print('Failed to open options menu:', e)

    def on_pre_enter(self):
        """Load landlord properties when screen is entered"""
        self.load_my_properties()
        self.load_activity()
    
    def load_my_properties(self):
        if hasattr(self.ids, 'my_properties_loading'):
            self.ids.my_properties_loading.text = 'Loading...'
        cached_request(API_BASE + 'landlord/properties/', on_success=self.on_properties_loaded, on_failure=self.on_properties_error)
    
    def on_properties_loaded(self, req, result):
        if hasattr(self.ids, 'my_properties_loading'):
            self.ids.my_properties_loading.text = ''
        
        if not hasattr(self.ids, 'my_properties_container'):
            return
        
        container = self.ids.my_properties_container
        container.clear_widgets()
        
        if not result or len(result) == 0:
            container.add_widget(Label(
                text='No properties yet. Add your first property!',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(60)
            ))
            return
        
        for prop in result:
            self.create_property_card(container, prop)
    
    def create_property_card(self, container, prop):
        """Create a property card for landlord's property list"""
        card = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(10)],
            spacing=dp(6),
            size_hint_y=None,
            height=dp(120)
        )
        
        from kivy.graphics import Color, RoundedRectangle
        with card.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(8)])
        card.bind(pos=lambda w, v: setattr(w.bg_rect, 'pos', v))
        card.bind(size=lambda w, v: setattr(w.bg_rect, 'size', v))
        
        title_label = Label(
            text=f"[b]{prop.get('title', 'Property')}[/b]",
            markup=True,
            color=(0, 0, 0, 1),
            font_size='15sp',
            size_hint_y=None,
            height=dp(25),
            halign='left',
            valign='top'
        )
        title_label.bind(size=title_label.setter('text_size'))
        
        status_text = '✓ Approved' if prop.get('is_approved') else '⏳ Pending Approval'
        status_color = (0, 0.6, 0, 1) if prop.get('is_approved') else (0.8, 0.5, 0, 1)
        
        status_label = Label(
            text=status_text,
            color=status_color,
            font_size='12sp',
            size_hint_y=None,
            height=dp(20),
            halign='left',
            valign='top'
        )
        status_label.bind(size=status_label.setter('text_size'))
        
        price_label = Label(
            text=f"${prop.get('nightly_price', 'N/A')} per night",
            color=(0.3, 0.3, 0.3, 1),
            font_size='13sp',
            size_hint_y=None,
            height=dp(20),
            halign='left',
            valign='top'
        )
        price_label.bind(size=price_label.setter('text_size'))
        
        card.add_widget(title_label)
        card.add_widget(status_label)
        card.add_widget(price_label)
        
        # Add tap handler
        from kivy.uix.behaviors import ButtonBehavior
        class CardButton(ButtonBehavior, BoxLayout):
            pass
        
        btn_card = CardButton()
        btn_card.add_widget(card)
        btn_card.bind(on_release=lambda _: self.view_property(prop.get('id')))
        container.add_widget(btn_card)
    
    def view_property(self, prop_id):
        """Navigate to property detail"""
        if hasattr(self.manager, 'get_screen'):
            detail_screen = self.manager.get_screen('property_detail')
            detail_screen.load_property(prop_id)
            self.manager.current = 'property_detail'
    
    def on_properties_error(self, req, error):
        if hasattr(self.ids, 'my_properties_loading'):
            self.ids.my_properties_loading.text = 'Failed to load properties. Please login.'

    def load_activity(self):
        if hasattr(self.ids, 'activity_loading'):
            self.ids.activity_loading.text = 'Loading...'
        cached_request(API_BASE + 'landlord/activity/', on_success=self.on_activity_loaded, on_failure=self.on_activity_error)

    def on_activity_loaded(self, req, result):
        if hasattr(self.ids, 'activity_loading'):
            self.ids.activity_loading.text = ''

        if not hasattr(self.ids, 'activity_container'):
            return

        container = self.ids.activity_container
        container.clear_widgets()

        rows = result if isinstance(result, list) else []
        if not rows:
            container.add_widget(Label(
                text='No inquiries yet.',
                color=(0.5, 0.5, 0.5, 1),
                font_size='13sp',
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle'
            ))
            return

        for row in rows[:30]:
            container.add_widget(self._create_activity_row(row))

    def _create_activity_row(self, row):
        wrap = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(10)],
            spacing=dp(4),
            size_hint_y=None,
            height=dp(86)
        )

        from kivy.graphics import Color, RoundedRectangle
        with wrap.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            wrap.bg_rect = RoundedRectangle(pos=wrap.pos, size=wrap.size, radius=[dp(8)])
        wrap.bind(pos=lambda w, v: setattr(w.bg_rect, 'pos', v))
        wrap.bind(size=lambda w, v: setattr(w.bg_rect, 'size', v))

        viewer = row.get('viewer_email') or row.get('viewer') or 'Unknown'
        title = row.get('property_title') or row.get('property') or 'Property'
        viewed_at = row.get('viewed_at') or row.get('created_at') or ''
        ts = self._format_ts(viewed_at)

        title_label = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            color=(0, 0, 0, 1),
            font_size='14sp',
            size_hint_y=None,
            height=dp(22),
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))

        viewer_label = Label(
            text=f"Viewer: {viewer}",
            color=(0.3, 0.3, 0.3, 1),
            font_size='12sp',
            size_hint_y=None,
            height=dp(18),
            halign='left',
            valign='middle'
        )
        viewer_label.bind(size=viewer_label.setter('text_size'))

        ts_label = Label(
            text=f"Viewed at: {ts}" if ts else "",
            color=(0.45, 0.45, 0.45, 1),
            font_size='12sp',
            size_hint_y=None,
            height=dp(18),
            halign='left',
            valign='middle'
        )
        ts_label.bind(size=ts_label.setter('text_size'))

        wrap.add_widget(title_label)
        wrap.add_widget(viewer_label)
        if ts:
            wrap.add_widget(ts_label)
        return wrap

    def _format_ts(self, value):
        if not value:
            return ''
        try:
            # Expecting ISO string from DRF
            dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return str(value)

    def on_activity_error(self, req, error):
        if hasattr(self.ids, 'activity_loading'):
            self.ids.activity_loading.text = 'Failed to load history. Please login.'
        if hasattr(self.ids, 'activity_container'):
            self.ids.activity_container.clear_widgets()
            self.ids.activity_container.add_widget(Label(
                text='Could not load inquiry history.',
                color=(0.5, 0.5, 0.5, 1),
                font_size='13sp',
                size_hint_y=None,
                height=dp(30),
                halign='left',
                valign='middle'
            ))


# Session Manager for persistent auth
class SessionManager:
    """Manages user session and auth state"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.user_data = None
            cls._instance.is_authenticated = False
        return cls._instance
    
    def set_user(self, user_data):
        """Store user data after login"""
        self.user_data = user_data
        self.is_authenticated = True
    
    def clear_user(self):
        """Clear user data on logout"""
        self.user_data = None
        self.is_authenticated = False
    
    def get_user(self):
        """Get current user data"""
        return self.user_data
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.is_authenticated


class LocationListScreen(Screen):
    """Screen showing list of cities for long-term accommodation"""
    
    def show_options_menu(self):
        """Show options menu - reuse from HomeScreen"""
        home_screen = self.manager.get_screen('home')
        home_screen.show_options_menu()
    
    def on_pre_enter(self):
        self.load_locations()
    
    def load_locations(self):
        """Load available cities from cities API"""
        if hasattr(self.ids, 'cities_loading'):
            self.ids.cities_loading.text = 'Loading...'
            start_pulse(self.ids.cities_loading)
        
        def on_success(req, result):
            if hasattr(self.ids, 'cities_loading'):
                self.ids.cities_loading.text = ''
                stop_pulse(self.ids.cities_loading)
            
            cities_grid = self.ids.get('cities_grid')
            if not cities_grid:
                return
            
            cities_grid.clear_widgets()
            
            cities = result if isinstance(result, list) else []

            # Create simple city cards
            for idx, city in enumerate(cities):
                card = self.create_city_card(city, idx)
                cities_grid.add_widget(card)

            if not cities:
                no_data = Label(
                    text='No long-term accommodations available yet',
                    color=[0.5, 0.5, 0.5, 1],
                    font_size=sp(14)
                )
                cities_grid.add_widget(no_data)
        
        def on_failure(req, error):
            if hasattr(self.ids, 'cities_loading'):
                self.ids.cities_loading.text = 'Failed to load'
                stop_pulse(self.ids.cities_loading)
            print(f"Failed to load cities: {error}")
        
        cached_request(
            f"{API_BASE}cities/?property_type=long_term&include_empty=1",
            on_success=on_success,
            on_failure=on_failure,
        )
    
    def create_city_card(self, city, index):
        """Create a simple, clean card for a city"""
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, RoundedRectangle, Line
        
        class CityCard(ButtonBehavior, BoxLayout):
            pass
        
        # Responsive sizing
        is_small = Window.width < dp(600)
        card_height = dp(70) if is_small else dp(80)
        font_size = sp(16) if is_small else sp(18)
        
        card = CityCard(
            orientation='horizontal',
            padding=[dp(24), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=card_height
        )
        card.opacity = 0
        
        # White background with light border
        with card.canvas.before:
            Color(1, 1, 1, 1)
            card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            Color(0.88, 0.88, 0.88, 1)
            card.border = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(12)), width=1.5)
        
        def update_graphics(instance, value):
            card.bg_rect.pos = instance.pos
            card.bg_rect.size = instance.size
            card.border.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(12))
        
        card.bind(pos=update_graphics, size=update_graphics)
        
        city_name = city.get('name', '') if isinstance(city, dict) else str(city)
        city_id = city.get('id') if isinstance(city, dict) else None
        count = city.get('properties_count') if isinstance(city, dict) else None

        # City name
        name_label = Label(
            text=f"[b]{city_name}[/b]",
            markup=True,
            font_size=font_size,
            color=[0.15, 0.15, 0.15, 1],
            halign='left',
            valign='middle'
        )
        name_label.bind(size=name_label.setter('text_size'))
        card.add_widget(name_label)
        
        # Spacer
        card.add_widget(Widget())
        
        # Optional count
        if isinstance(count, int):
            count_label = Label(
                text=f"{count} places",
                font_size=sp(12) if is_small else sp(13),
                color=[0.45, 0.45, 0.45, 1],
                size_hint_x=None,
                width=dp(90),
                halign='right',
                valign='middle'
            )
            count_label.bind(size=count_label.setter('text_size'))
            card.add_widget(count_label)

        # Arrow
        arrow = Label(
            text='→',
            font_size=sp(28) if is_small else sp(32),
            color=[0.6, 0.6, 0.6, 1],
            size_hint_x=None,
            width=dp(40),
            halign='right',
            valign='middle'
        )
        arrow.bind(size=arrow.setter('text_size'))
        card.add_widget(arrow)
        
        # Click handler
        def on_click(_):
            props_screen = self.manager.get_screen('properties')
            if city_id is not None:
                props_screen.load_for_city(city_id, city_name)
            else:
                # Fallback for older payloads
                props_screen.load_for_city(None, city_name)
            self.manager.current = 'properties'
        
        card.bind(on_release=on_click)
        fade_in_widget(card, delay=index * 0.05)
        
        return card


class ShortTermScreen(Screen):
    """Airbnb-style city selection for short-term accommodations"""

    def on_pre_enter(self):
        self.load_cities()

    def load_cities(self):
        def on_success(req, result):
            grid = self.ids.get('cities_grid')
            if not grid:
                return
            grid.clear_widgets()
            cities = result if isinstance(result, list) else []
            for idx, city in enumerate(cities):
                card = self._create_city_card(city, idx, on_select=self.open_city)
                grid.add_widget(card)
        
        def on_failure(req, error):
            print(f"Failed to load short-term cities: {error}")

        cached_request(
            f"{API_BASE}cities/?property_type=short_term&include_empty=1",
            on_success=on_success,
            on_failure=on_failure,
        )

    def open_city(self, city):
        props = self.manager.get_screen('service_properties')
        props.load(property_type='short_term', city_id=city.get('id'), city_name=city.get('name'), heading_prefix='Short-term stays', back_screen='short_term')
        self.manager.current = 'service_properties'

    def _create_city_card(self, city, index, on_select):
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.graphics import Color, RoundedRectangle, Line

        class CityCard(ButtonBehavior, BoxLayout):
            pass

        is_small = Window.width < dp(600)
        card_height = dp(70) if is_small else dp(80)
        font_size = sp(16) if is_small else sp(18)

        card = CityCard(
            orientation='horizontal',
            padding=[dp(24), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
            height=card_height,
        )
        card.opacity = 0

        with card.canvas.before:
            Color(1, 1, 1, 1)
            card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            Color(0.88, 0.88, 0.88, 1)
            card.border = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(12)), width=1.5)

        def update_graphics(instance, _value):
            card.bg_rect.pos = instance.pos
            card.bg_rect.size = instance.size
            card.border.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(12))

        card.bind(pos=update_graphics, size=update_graphics)

        name = city.get('name', 'City')
        count = city.get('properties_count', 0)
        name_label = Label(
            text=f"[b]{name}[/b]",
            markup=True,
            font_size=font_size,
            color=[0.15, 0.15, 0.15, 1],
            halign='left',
            valign='middle',
        )
        name_label.bind(size=name_label.setter('text_size'))
        card.add_widget(name_label)
        card.add_widget(Widget())

        count_label = Label(
            text=f"{count} places",
            font_size=sp(12) if is_small else sp(13),
            color=[0.45, 0.45, 0.45, 1],
            size_hint_x=None,
            width=dp(90),
            halign='right',
            valign='middle',
        )
        count_label.bind(size=count_label.setter('text_size'))
        card.add_widget(count_label)

        arrow = Label(
            text='→',
            font_size=sp(28) if is_small else sp(32),
            color=[0.6, 0.6, 0.6, 1],
            size_hint_x=None,
            width=dp(40),
            halign='right',
            valign='middle',
        )
        arrow.bind(size=arrow.setter('text_size'))
        card.add_widget(arrow)

        card.bind(on_release=lambda _btn: on_select(city))
        fade_in_widget(card, delay=index * 0.05)
        return card


class RealEstateScreen(Screen):
    """City selection screen for Real estate / Lodges / Resorts / Shops"""

    def on_pre_enter(self):
        self.load_cities()

    def load_cities(self):
        def on_success(req, result):
            grid = self.ids.get('cities_grid')
            if not grid:
                return
            grid.clear_widgets()
            cities = result if isinstance(result, list) else []
            for idx, city in enumerate(cities):
                card = self._create_city_card(city, idx)
                grid.add_widget(card)

        def on_failure(req, error):
            print(f"Failed to load real estate cities: {error}")

        cached_request(
            f"{API_BASE}cities/?property_types=resort,real_estate,shop&include_empty=1&include_breakdown=1",
            on_success=on_success,
            on_failure=on_failure,
        )

    def _create_city_card(self, city, index):
        # Reuse ShortTermScreen's city card styling
        return ShortTermScreen._create_city_card(self, city, index, on_select=self.open_city)

    def open_city(self, city):
        props = self.manager.get_screen('service_properties')
        props.load(property_types=['resort', 'real_estate', 'shop'], city_id=city.get('id'), city_name=city.get('name'), heading_prefix='Real estate', back_screen='real_estate')
        self.manager.current = 'service_properties'


class ResortsScreen(Screen):
    """City selection for resort stays"""

    def on_pre_enter(self):
        self.load_cities()

    def load_cities(self):
        def on_success(req, result):
            grid = self.ids.get('cities_grid')
            if not grid:
                return
            grid.clear_widgets()
            cities = result if isinstance(result, list) else []
            for idx, city in enumerate(cities):
                grid.add_widget(ShortTermScreen._create_city_card(self, city, idx, on_select=self.open_city))

        def on_failure(req, error):
            print(f"Failed to load resort cities: {error}")

        cached_request(
            f"{API_BASE}cities/?property_type=resort&include_empty=1",
            on_success=on_success,
            on_failure=on_failure,
        )

    def open_city(self, city):
        props = self.manager.get_screen('service_properties')
        props.load(property_type='resort', city_id=city.get('id'), city_name=city.get('name'), heading_prefix='Resorts', back_screen='resorts')
        self.manager.current = 'service_properties'


class ShopsScreen(Screen):
    """City selection for shops"""

    def on_pre_enter(self):
        self.load_cities()

    def load_cities(self):
        def on_success(req, result):
            grid = self.ids.get('cities_grid')
            if not grid:
                return
            grid.clear_widgets()
            cities = result if isinstance(result, list) else []
            for idx, city in enumerate(cities):
                grid.add_widget(ShortTermScreen._create_city_card(self, city, idx, on_select=self.open_city))

        def on_failure(req, error):
            print(f"Failed to load shop cities: {error}")

        cached_request(
            f"{API_BASE}cities/?property_type=shop&include_empty=1",
            on_success=on_success,
            on_failure=on_failure,
        )

    def open_city(self, city):
        props = self.manager.get_screen('service_properties')
        props.load(property_type='shop', city_id=city.get('id'), city_name=city.get('name'), heading_prefix='Shops', back_screen='shops')
        self.manager.current = 'service_properties'


class ServicePropertiesScreen(Screen):
    """Shared properties list for service flows (city -> properties -> detail)."""

    back_screen = 'home'

    property_type = None
    property_types = None
    city_id = None
    city_name = None

    def load(self, *, property_type=None, property_types=None, city_id=None, city_name=None, heading_prefix='Properties', back_screen='home'):
        self.property_type = property_type
        self.property_types = property_types
        self.city_id = city_id
        self.city_name = city_name
        self.back_screen = back_screen or 'home'

        if hasattr(self.ids, 'service_heading'):
            suffix = f" in {city_name}" if city_name else ""
            self.ids.service_heading.text = f"{heading_prefix}{suffix}"

        self.load_properties()

    def go_back(self):
        try:
            if self.manager and self.back_screen in self.manager.screen_names:
                self.manager.current = self.back_screen
            else:
                self.manager.current = 'home'
        except Exception:
            self.manager.current = 'home'

    def load_properties(self):
        grid = self.ids.get('properties_grid')
        if grid:
            grid.clear_widgets()

        def on_success(req, result):
            grid = self.ids.get('properties_grid')
            if not grid:
                return
            grid.clear_widgets()

            items = result.get('results', []) if isinstance(result, dict) else (result if isinstance(result, list) else [])

            if not items:
                grid.add_widget(Label(text='No listings yet', color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(40)))
                return

            for idx, prop in enumerate(items):
                card = self.create_property_card(prop)
                grid.add_widget(card)
                fade_in_widget(card, delay=idx * 0.03)

        def on_failure(req, error):
            print(f"Failed to load properties: {error}")

        url = f"{API_BASE}properties/?"
        if self.property_type:
            url += f"property_type={self.property_type}"
        elif self.property_types:
            url += f"property_types={','.join(self.property_types)}"
        if self.city_id is not None:
            url += f"&city_id={self.city_id}"

        cached_request(url, on_success=on_success, on_failure=on_failure)

    def create_property_card(self, prop):
        """Create a web-like accommodation card (same structure as PropertyListScreen)."""
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, RoundedRectangle, Line

        class PropertyCard(ButtonBehavior, BoxLayout):
            pass

        w = Window.width
        is_small = w < dp(600)

        card_height = dp(332) if is_small else dp(350)
        media_h = dp(200) if is_small else dp(220)

        card = PropertyCard(orientation='vertical', size_hint_y=None, height=card_height, padding=0, spacing=0)
        card.opacity = 0

        with card.canvas.before:
            Color(0, 0, 0, 0.08)
            card.shadow_rect = RoundedRectangle(pos=(card.x, card.y - dp(4)), size=card.size, radius=[dp(22)])
            Color(1, 1, 1, 1)
            card.bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(22)])
        with card.canvas.after:
            Color(0.937, 0.902, 0.851, 1)
            card.border_line = Line(rounded_rectangle=[card.x, card.y, card.width, card.height, dp(22)], width=1)

        def _sync(_inst, _val):
            card.shadow_rect.pos = (card.x, card.y - dp(4))
            card.shadow_rect.size = card.size
            card.bg_rect.pos = card.pos
            card.bg_rect.size = card.size
            card.border_line.rounded_rectangle = [card.x, card.y, card.width, card.height, dp(22)]

        card.bind(pos=_sync, size=_sync)

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(58), padding=[dp(14), dp(10)], spacing=dp(10))

        avatar = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)))
        with avatar.canvas.before:
            Color(1.0, 0.976, 0.949, 1)
            avatar.bg = RoundedRectangle(pos=avatar.pos, size=avatar.size, radius=[dp(14)])
            Color(0.878, 0.847, 0.780, 1)
            avatar.bd = Line(rounded_rectangle=[avatar.x, avatar.y, avatar.width, avatar.height, dp(14)], width=1.2)
        avatar.bind(pos=lambda i, v: setattr(i.bg, 'pos', v))
        avatar.bind(size=lambda i, v: setattr(i.bg, 'size', v))
        avatar.bind(pos=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(14)]))
        avatar.bind(size=lambda i, _v: setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(14)]))

        thumb = (prop or {}).get('thumbnail') or ''
        if thumb:
            avatar.add_widget(AsyncImage(source=thumb, fit_mode='contain'))
        else:
            avatar.add_widget(Label(text='🏠', font_size=sp(18), color=(0.55, 0.55, 0.55, 1), halign='center', valign='middle'))
            avatar.children[0].bind(size=avatar.children[0].setter('text_size'))
        header.add_widget(avatar)

        meta = BoxLayout(orientation='vertical', spacing=dp(2))

        location_text = ''
        if (prop or {}).get('location'):
            location_text = str(prop.get('location'))
        elif (prop or {}).get('city'):
            location_text = str(prop.get('city'))
        elif self.city_name:
            location_text = str(self.city_name)
        else:
            location_text = 'Available listing'

        channel = Label(
            text=location_text,
            font_size=sp(12) if is_small else sp(13),
            color=(0.25, 0.25, 0.25, 1),
            halign='left',
            valign='middle',
        )
        channel.bind(size=channel.setter('text_size'))
        meta.add_widget(channel)

        ptype = (prop or {}).get('property_type') or ''
        meta_line = ptype.replace('_', ' ').title() if ptype else ''
        followers = Label(
            text=meta_line,
            font_size=sp(11) if is_small else sp(12),
            color=(0.45, 0.45, 0.45, 1),
            halign='left',
            valign='middle',
        )
        followers.bind(size=followers.setter('text_size'))
        meta.add_widget(followers)
        header.add_widget(meta)

        like_btn = Button(
            text='♥' if self.is_liked((prop or {}).get('id')) else '♡',
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            background_normal='',
            background_color=[1, 1, 1, 1],
            font_size=sp(20),
            color=[1, 0.2, 0.2, 1] if self.is_liked((prop or {}).get('id')) else [0.25, 0.25, 0.25, 1],
        )
        with like_btn.canvas.before:
            Color(1, 1, 1, 0.9)
            like_btn.bg = RoundedRectangle(pos=like_btn.pos, size=like_btn.size, radius=[dp(21)])
            Color(0.90, 0.90, 0.90, 1)
            like_btn.bd = Line(rounded_rectangle=[like_btn.x, like_btn.y, like_btn.width, like_btn.height, dp(21)], width=1)
        like_btn.bind(pos=lambda i, _v: (setattr(i.bg, 'pos', i.pos), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(21)])))
        like_btn.bind(size=lambda i, _v: (setattr(i.bg, 'size', i.size), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(21)])))
        like_btn.bind(on_release=lambda btn, p=prop: self.toggle_like(p, btn))
        header.add_widget(Widget())
        header.add_widget(like_btn)

        card.add_widget(header)

        media = BoxLayout(size_hint_y=None, height=media_h)
        img_src = (prop or {}).get('thumbnail') or 'assets/placeholder.png'
        media_img = AsyncImage(source=img_src)
        configure_cover_image(media_img)
        media.add_widget(media_img)
        card.add_widget(media)

        body = BoxLayout(orientation='vertical', padding=[dp(12), dp(10)], spacing=dp(6))
        title_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(8))

        title = Label(
            text=str((prop or {}).get('title') or 'Property'),
            font_size=sp(14) if is_small else sp(15),
            bold=True,
            color=(0.13, 0.13, 0.13, 1),
            halign='left',
            valign='middle',
        )
        if hasattr(title, 'shorten'):
            title.shorten = True
            title.shorten_from = 'right'
        title.bind(size=title.setter('text_size'))
        title_row.add_widget(title)

        is_monthly = ptype in ('long_term', 'shop')
        if is_monthly:
            amount = (prop or {}).get('price_per_month')
            suffix = '/month'
        else:
            amount = (prop or {}).get('nightly_price')
            suffix = '/night'
        amount_text = str(amount) if amount not in (None, '') else 'N/A'

        pill = Label(
            text=f"🔥 ${amount_text} {suffix}",
            font_size=sp(11) if is_small else sp(12),
            color=(0.13, 0.13, 0.13, 1),
            halign='center',
            valign='middle',
            size_hint=(None, None),
            size=(dp(120), dp(26)),
        )
        pill.bind(size=pill.setter('text_size'))
        with pill.canvas.before:
            Color(1, 0.976, 0.953, 1)
            pill.bg = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(13)])
            Color(1, 0.894, 0.776, 1)
            pill.bd = Line(rounded_rectangle=[pill.x, pill.y, pill.width, pill.height, dp(13)], width=1)
        pill.bind(pos=lambda i, _v: (setattr(i.bg, 'pos', i.pos), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(13)])))
        pill.bind(size=lambda i, _v: (setattr(i.bg, 'size', i.size), setattr(i.bd, 'rounded_rectangle', [i.x, i.y, i.width, i.height, dp(13)])))

        title_row.add_widget(pill)
        body.add_widget(title_row)

        desc_text = str((prop or {}).get('description') or '')
        if len(desc_text) > 110:
            desc_text = desc_text[:107] + '...'
        if desc_text:
            desc = Label(
                text=desc_text,
                font_size=sp(12) if is_small else sp(13),
                color=(0.35, 0.35, 0.35, 1),
                halign='left',
                valign='top',
                size_hint_y=None,
                height=dp(44),
            )
            desc.bind(size=desc.setter('text_size'))
            body.add_widget(desc)

        read_more = Label(
            text='Read more',
            font_size=sp(12),
            bold=True,
            color=(0.05, 0.43, 0.99, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(18),
        )
        read_more.bind(size=read_more.setter('text_size'))
        body.add_widget(read_more)

        card.add_widget(body)

        def on_click(_):
            det = self.manager.get_screen('property_detail')
            det.load_property(prop.get('id'))
            self.manager.current = 'property_detail'

        card.bind(on_release=on_click)
        return card

    def is_liked(self, prop_id):
        return str(prop_id) in self.liked_store

    def toggle_like(self, prop, btn):
        prop_id = str(prop.get('id'))
        if self.is_liked(prop_id):
            self.liked_store.delete(prop_id)
            btn.text = '♡'
            btn.color = [0.8, 0.2, 0.2, 1]
        else:
            self.liked_store.put(prop_id, liked=True, prop=prop)
            btn.text = '♥'
            btn.color = [1, 0.2, 0.2, 1]


sm = None


class OffRezApp(App):
    # Exposed to KV so we can show web-like navbar items conditionally.
    is_authenticated = BooleanProperty(False)
    # Font used for unicode/emoji icons in headers (e.g., bell/menu). On Windows
    # the default Kivy font may not include these glyphs.
    icon_font = StringProperty('')

    def _detect_icon_font(self):
        try:
            # Prefer Windows emoji font if available.
            candidates = [
                r"C:\\Windows\\Fonts\\seguiemj.ttf",  # Segoe UI Emoji
                r"C:\\Windows\\Fonts\\seguisym.ttf",  # Segoe UI Symbol
            ]
            for p in candidates:
                if os.path.exists(p):
                    self.icon_font = p
                    return
        except Exception:
            pass
        self.icon_font = ''

    def load_kv(self, filename=None):
        # Load KV after the App instance exists so `app.*` bindings can bind.
        global KV_LOAD_ERROR

        if getattr(self, '_offrez_kv_loaded', False):
            return

        def _load_one(path: str, label: str):
            if not os.path.exists(path):
                print(f'{label} KV file not found at', path)
                return
            if path in getattr(Builder, 'files', []):
                return
            try:
                Builder.load_file(path)
            except Exception:
                log_path = os.path.join(os.path.dirname(__file__), 'offrez_kv_error.log')
                with open(log_path, 'a', encoding='utf-8') as fh:
                    fh.write(f"{datetime.utcnow().isoformat()} - KV load error ({label}):\n")
                    fh.write(traceback.format_exc())
                    fh.write('\n---\n')
                print('Failed to load', label, 'KV; wrote traceback to', log_path)
                KV_LOAD_ERROR = log_path

        _load_one(KV_PATH, 'main')
        _load_one(EXTRA_KV_PATH, 'extra')
        self._offrez_kv_loaded = True

    def refresh_auth_state(self):
        try:
            session = SessionManager()
            self.is_authenticated = bool(session.is_logged_in())
        except Exception:
            self.is_authenticated = False

    def open_web_path(self, path: str):
        """Open a web route (e.g. /about/) in the system browser."""
        try:
            base = API_BASE
            if '/api/' in base:
                base = base.split('/api/', 1)[0] + '/'
            path = (path or '').lstrip('/')
            url = urllib.parse.urljoin(base, path)
            webbrowser.open(url)
        except Exception as e:
            print('Failed to open web url:', e)

    def open_about(self):
        self.open_web_path('about/')

    def open_contact(self):
        self.open_web_path('contact/')

    def build(self):
        self._detect_icon_font()
        self.refresh_auth_state()
        global sm

        # Build screens after KV is loaded so widget rules/ids are applied.
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(UniversitiesScreen(name='universities'))
        sm.add_widget(PropertyListScreen(name='properties'))
        sm.add_widget(PropertyDetailScreen(name='property_detail'))
        sm.add_widget(PropertyContactScreen(name='property_contact'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(ChangePasswordScreen(name='change_password'))
        sm.add_widget(NotificationsScreen(name='notifications'))
        sm.add_widget(MyPropertiesScreen(name='my_properties'))
        sm.add_widget(LocationListScreen(name='location_list'))
        sm.add_widget(ShortTermScreen(name='short_term'))
        sm.add_widget(RealEstateScreen(name='real_estate'))
        sm.add_widget(ResortsScreen(name='resorts'))
        sm.add_widget(ShopsScreen(name='shops'))
        sm.add_widget(ServicePropertiesScreen(name='service_properties'))

        # explicitly ensure the screen manager shows the home screen
        sm.current = 'home'
        print('App build complete; current screen =', sm.current)
        return sm

    def go_profile(self):
        session = SessionManager()
        if session.is_logged_in():
            self.root.current = 'profile'
        else:
            self.root.current = 'login'

    def go_notifications(self):
        session = SessionManager()
        if session.is_logged_in():
            self.root.current = 'notifications'
        else:
            self.root.current = 'login'

    def show_options_menu(self):
        home = self.root.get_screen('home')
        home.show_options_menu()

    def do_logout(self):
        # Best effort server logout; always clear local session.
        session = SessionManager()

        def _done(*_args):
            session.clear_user()
            self.refresh_auth_state()
            self.root.current = 'home'

        try:
            UrlRequest(
                API_AUTH_BASE + 'logout/',
                on_success=lambda *_: _done(),
                on_error=lambda *_: _done(),
                on_failure=lambda *_: _done(),
                method='POST',
            )
        except Exception:
            _done()


if __name__ == '__main__':
    OffRezApp().run()

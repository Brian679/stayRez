"""
Generate placeholder images for the service tiles
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create assets directory if it doesn't exist
os.makedirs('assets', exist_ok=True)

# Define services with their colors
services = [
    ('students.png', 'Students\nAccommodation', (25, 25, 112)),  # Midnight blue
    ('longterm.png', 'Long-term\nAccommodation', (34, 139, 34)),  # Forest green
    ('shortterm.png', 'Short-term\nAccommodation', (255, 140, 0)),  # Dark orange
    ('realestate.png', 'Real Estate', (220, 20, 60)),  # Crimson
    ('resorts.png', 'Resorts', (0, 191, 255)),  # Deep sky blue
    ('shops.png', 'Shops to Rent', (148, 0, 211))  # Dark violet
]

# Image dimensions
width, height = 400, 300

for filename, text, color in services:
    # Create image with solid color
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Add lighter overlay for better text visibility
    overlay = Image.new('RGBA', (width, height), (*color, 200))
    img.paste(overlay, (0, 0), overlay)
    
    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 48)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Add white text with shadow for better visibility
    # Shadow
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 128), font=font, align='center')
    # Main text
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Add decorative icon/symbol at top
    icon_y = 30
    draw.ellipse([width//2 - 30, icon_y, width//2 + 30, icon_y + 60], fill='white', outline=color, width=3)
    
    # Save image
    filepath = os.path.join('assets', filename)
    img.save(filepath)
    print(f"Created {filepath}")

print("\nAll placeholder images created successfully!")
print("You can replace these with real images later.")

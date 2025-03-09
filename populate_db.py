import requests
import time
import random

# Configuration
API_URL = "http://localhost:8000/upload-clothing/description"
USER_ID = "test-user-91f1b146" # put a valid userId that is already in the users table

# Get vocabulary lists directly from the ML model
def get_color_list():
    """Return the list of common clothing colors the ML model looks for."""
    return [
        'red', 'blue', 'green', 'yellow', 'black', 'white', 'grey', 'gray',
        'purple', 'pink', 'orange', 'brown', 'navy', 'beige', 'cream', 'tan',
        'olive', 'burgundy', 'charcoal', 'silver', 'gold', 'teal', 'khaki',
        'maroon', 'mustard', 'coral', 'mint', 'turquoise', 'indigo', 'magenta',
        'lavender', 'peach', 'rust', 'emerald', 'ochre', 'crimson', 'azure',
        'lilac', 'amber', 'salmon', 'slate', 'mauve', 'taupe', 'cerulean',
        'ivory', 'camel', 'sage', 'periwinkle', 'plum', 'cobalt', 'fuchsia'
    ]

def get_material_list():
    """Return the list of common clothing materials the ML model looks for."""
    return [
        'cotton', 'wool', 'leather', 'denim', 'silk', 'linen', 'polyester',
        'nylon', 'cashmere', 'velvet', 'suede', 'corduroy', 'fleece', 'tweed',
        'jersey', 'canvas', 'chino', 'flannel', 'chenille', 'satin', 'viscose',
        'spandex', 'rayon', 'acrylic', 'lyocell', 'mohair', 'merino', 'angora',
        'modal', 'twill', 'chambray', 'terry', 'mesh', 'sequin', 'bamboo',
        'microfiber', 'gabardine', 'herringbone', 'poplin', 'organza', 'taffeta',
        'fur', 'faux fur', 'sherpa', 'crepe', 'lamé', 'oxford', 'gore-tex'
    ]

def get_top_types():
    """Return clothing type terms for tops that the ML model recognizes."""
    return [
        't-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt', 'hoodie', 
        'polo', 'tank', 'turtleneck', 'tunic', 'button-down',
        'henley', 'crop top', 'camisole', 'pullover', 'jersey', 'long sleeve',
        'short sleeve', 'v-neck', 'crew neck', 'sleeveless', 'top', 'cardigan'
    ]

def get_bottom_types():
    """Return clothing type terms for bottoms that the ML model recognizes."""
    return [
        'jeans', 'pants', 'trousers', 'shorts', 'skirt', 'chinos', 'leggings',
        'joggers', 'sweatpants', 'culottes', 'capris', 'jeggings', 'cargo',
        'khakis', 'slacks', 'dress pants', 'bermudas', 'palazzo', 'linen pants'
    ]

def get_onepiece_types():
    """Return clothing type terms for one-piece items that the ML model recognizes."""
    return [
        'dress', 'jumpsuit', 'romper', 'playsuit', 'gown', 'sundress', 'maxi',
        'midi', 'mini', 'shift', 'sheath', 'a-line', 'wrap', 'slip dress'
    ]

def get_outerwear_types():
    """Return clothing type terms for outerwear that the ML model recognizes."""
    return [
        'jacket', 'coat', 'blazer', 'parka', 'windbreaker', 'vest', 
        'trench', 'bomber', 'denim jacket', 'leather jacket', 'puffer', 'raincoat',
        'poncho', 'peacoat', 'overcoat', 'anorak', 'cape', 'shrug'
    ]

def get_footwear_types():
    """Return clothing type terms for footwear that the ML model recognizes."""
    return [
        'shoes', 'boots', 'sneakers', 'sandals', 'loafers', 'flats', 'heels',
        'pumps', 'wedges', 'oxford shoes', 'slippers', 'mules', 'espadrilles',
        'mocassins', 'brogues', 'ankle boots', 'hiking boots', 'slip-ons'
    ]

def get_accessory_types():
    """Return clothing type terms for accessories that the ML model recognizes."""
    return [
        'watch', 'scarf', 'tie', 'belt', 'hat', 'gloves', 'socks', 'necklace',
        'earrings', 'bracelet', 'ring', 'sunglasses', 'bag', 'purse', 'handbag',
        'wallet', 'backpack', 'tote', 'clutch', 'headband', 'beanie', 'cap',
        'beret', 'bowtie', 'pocket square', 'cufflinks', 'anklet', 'brooch'
    ]

def get_patterns():
    """Return patterns that the ML model recognizes."""
    return [
        'solid', 'striped', 'plaid', 'floral', 'polka dot', 'animal print',
        'geometric', 'print', 'colorblock', 'check', 'checked', 'tartan',
        'herringbone', 'paisley', 'chevron', 'pinstripe', 'gingham'
    ]

def get_fits():
    """Return fit descriptions that the ML model recognizes."""
    return [
        'slim', 'fitted', 'tailored', 'skinny', 'tight', 'form-fitting',
        'regular', 'classic', 'standard', 'straight', 'normal',
        'loose', 'relaxed', 'oversized', 'baggy', 'wide', 'boxy'
    ]

def get_formality_terms():
    """Return formality-related terms that the ML model recognizes."""
    return {
        'casual': ['casual', 'relaxed', 'everyday', 'laid back', 'easygoing', 'comfortable', 'lounging', 'weekend', 'home', 'errands'],
        'business': ['business', 'work', 'office', 'professional', 'business casual', 'interview', 'presentation', 'networking', 'conference'],
        'formal': ['formal', 'elegant', 'sophisticated', 'dressy', 'wedding', 'black tie', 'ceremony', 'cocktail', 'dinner', 'graduation']
    }

def get_seasonality_terms():
    """Return seasonality-related terms that the ML model recognizes."""
    return {
        'summer': ['summer', 'hot', 'warm', 'lightweight', 'breathable', 'cooling', 'airy', 'tropical'],
        'winter': ['winter', 'cold', 'freezing', 'warm', 'insulated', 'heavy', 'thick', 'cozy', 'thermal'],
        'spring': ['spring', 'light', 'rain-resistant', 'transitional', 'mild'],
        'fall': ['fall', 'autumn', 'layering', 'mid-weight', 'moderate']
    }

def get_style_terms():
    """Return style profile terms that the ML model recognizes."""
    return {
        'casual': ['relaxed', 'comfortable', 'casual', 'laid back', 'easygoing'],
        'formal': ['elegant', 'sophisticated', 'formal', 'dressy', 'polished'],
        'business': ['professional', 'business', 'office', 'work', 'corporate'],
        'sporty': ['athletic', 'sporty', 'active', 'workout', 'gym'],
        'bohemian': ['boho', 'bohemian', 'artistic', 'free-spirited', 'earthy'],
        'vintage': ['retro', 'vintage', 'classic', 'old-fashioned', 'timeless'],
        'preppy': ['preppy', 'clean-cut', 'collegiate', 'traditional', 'nautical'],
        'streetwear': ['urban', 'street', 'trendy', 'hip', 'skater'],
        'minimalist': ['minimal', 'simple', 'clean', 'basic', 'understated']
    }

# Generate clothing descriptions directly based on the ML model's vocabulary
def generate_clothing_items(count=300):
    """Generate clothing descriptions using terms the ML model recognizes."""
    items = []
    
    # Get all the vocabulary lists
    colors = get_color_list()
    materials = get_material_list()
    patterns = get_patterns()
    fits = get_fits()
    
    formality_terms = get_formality_terms()
    all_formality = [term for terms in formality_terms.values() for term in terms]
    
    seasonality_terms = get_seasonality_terms()
    all_seasonality = [term for terms in seasonality_terms.values() for term in terms]
    
    style_terms = get_style_terms()
    all_styles = [term for terms in style_terms.values() for term in terms]
    
    # Category distribution (approximate percentage of wardrobe)
    category_distribution = {
        'top': 0.30,       # 30%
        'bottom': 0.20,    # 20%
        'one_piece': 0.10, # 10%
        'outerwear': 0.15, # 15%
        'footwear': 0.15,  # 15%
        'accessory': 0.10  # 10%
    }
    
    # Calculate how many items per category
    items_per_category = {
        category: int(count * percentage)
        for category, percentage in category_distribution.items()
    }
    
    # Adjust to ensure we get exactly the requested count
    total = sum(items_per_category.values())
    if total < count:
        items_per_category['top'] += count - total
    
    # Type lists by category
    type_by_category = {
        'top': get_top_types(),
        'bottom': get_bottom_types(),
        'one_piece': get_onepiece_types(),
        'outerwear': get_outerwear_types(),
        'footwear': get_footwear_types(),
        'accessory': get_accessory_types()
    }
    
    # Generate items for each category
    for category, num_items in items_per_category.items():
        category_types = type_by_category[category]
        
        for _ in range(num_items):
            # Always include color and type
            color = random.choice(colors)
            item_type = random.choice(category_types)
            
            # Include material most of the time (90%)
            if random.random() < 0.9:
                material = random.choice(materials)
                description = f"{color} {material} {item_type}"
            else:
                description = f"{color} {item_type}"
            
            # Add fit description sometimes (70%)
            if random.random() < 0.7:
                fit = random.choice(fits)
                description = f"{fit} {description}"
            
            # Add pattern sometimes (50%)
            if random.random() < 0.5:
                pattern = random.choice(patterns)
                description += f" with {pattern} pattern"
            
            # Add formality sometimes (40%)
            if random.random() < 0.4:
                formality = random.choice(all_formality)
                description += f" for {formality} occasions"
            
            # Add seasonality sometimes (30%)
            if random.random() < 0.3:
                seasonality = random.choice(all_seasonality)
                description += f", {seasonality} weather"
            
            # Add style sometimes (20%)
            if random.random() < 0.2:
                style = random.choice(all_styles)
                description += f", {style} style"
            
            items.append((description, category))
    
    # Shuffle the items for a more natural distribution
    random.shuffle(items)
    return items

# Function to add a clothing item
def add_clothing_item(description):
    payload = {
        "userId": USER_ID,
        "description": description
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Main execution
def main():
    total_items = 300
    print(f"Generating {total_items} clothing items using ML model vocabulary...")
    
    clothing_items = generate_clothing_items(total_items)
    
    print(f"Adding {len(clothing_items)} clothing items to the database for user {USER_ID}...")
    
    success_count = 0
    error_count = 0
    
    for i, (item, category) in enumerate(clothing_items, 1):
        try:
            # Print progress
            print(f"[{i}/{len(clothing_items)}] Adding {category}: {item}")
            
            result = add_clothing_item(item)
            
            if "error" in result:
                print(f"  Error: {result['error']}")
                error_count += 1
            else:
                success_count += 1
            
            # Small delay to prevent overwhelming the server
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  Exception: {str(e)}")
            error_count += 1
    
    print(f"\nSummary:")
    print(f"Successfully added: {success_count} items")
    print(f"Failed to add: {error_count} items")
    print(f"Total: {len(clothing_items)} items")

if __name__ == "__main__":
    main()
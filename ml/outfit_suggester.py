import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import spacy
import re
from typing import List, Dict, Any, Tuple
import pickle
import os
import joblib
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from collections import Counter

# Load spaCy model for NLP processing
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # If not installed, suggest installation
    print("Please install spaCy and the English model with:")
    print("pip install spacy")
    print("python -m spacy download en_core_web_sm")
    raise

class OutfitSuggester:
    def __init__(self, models_path=None):
        # Initialize feature extractors with expanded vocabularies
        self.color_vectorizer = TfidfVectorizer(vocabulary=self._get_color_list())
        self.material_vectorizer = TfidfVectorizer(vocabulary=self._get_material_list())
        self.type_vectorizer = TfidfVectorizer(vocabulary=self._get_clothing_types())
        
        # Fit the vectorizers with sample data
        self.color_vectorizer.fit([" ".join(self._get_color_list())])
        self.material_vectorizer.fit([" ".join(self._get_material_list())])
        self.type_vectorizer.fit([" ".join(self._get_clothing_types())])
        
        # Expanded weather categories
        self.weather_categories = {
            'hot': ['sunny', 'hot', 'warm', 'clear', 'heat', 'heatwave', 'scorching', 'tropical'],
            'cold': ['cold', 'freezing', 'chilly', 'snow', 'icy', 'frost', 'frigid', 'wintry'],
            'wet': ['rain', 'rainy', 'shower', 'drizzle', 'thunderstorm', 'downpour', 'humid', 'moisture'],
            'windy': ['windy', 'breezy', 'gusty', 'gale', 'draft', 'stormy', 'cyclone'],
            'mild': ['mild', 'pleasant', 'partly cloudy', 'cloudy', 'moderate', 'temperate', 'fair']
        }
        
        # Expanded occasion formality scores (1-10)
        self.occasion_formality = {
            'casual': 1,
            'everyday': 2, 
            'lounging': 1,
            'weekend': 2,
            'home': 1,
            'errands': 2,
            'work': 5,
            'office': 6,
            'business': 7,
            'business casual': 5,
            'date': 6,
            'party': 5,
            'celebration': 6,
            'ceremony': 8,
            'formal': 8,
            'wedding': 9,
            'black tie': 10,
            'interview': 8,
            'presentation': 7,
            'networking': 6,
            'conference': 6,
            'funeral': 9,
            'graduation': 7,
            'concert': 4,
            'dinner': 6,
            'brunch': 4,
            'cocktail': 7
        }
        
        # Initialize feature importance trackers
        self.feature_importance = {
            'color': 0.2,
            'material': 0.2,
            'type': 0.2,
            'formality': 0.25,
            'seasonality': 0.15
        }
        
        # Style profiles - patterns that match different styles
        self.style_profiles = {
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
        
        # Color coordination rules
        self.color_coordination = {
            'complementary': {
                'red': ['green', 'navy'],
                'blue': ['orange', 'rust', 'tan'],
                'yellow': ['purple', 'navy', 'gray'],
                'green': ['red', 'burgundy', 'pink'],
                'purple': ['yellow', 'gold', 'beige'],
                'orange': ['blue', 'navy', 'teal']
            },
            'monochromatic': {
                'black': ['black', 'white', 'gray', 'charcoal', 'silver'],
                'white': ['white', 'black', 'cream', 'gray', 'silver'],
                'navy': ['navy', 'white', 'blue', 'gray', 'red'],
                'gray': ['gray', 'black', 'white', 'silver', 'charcoal']
            },
            'neutral_base': ['black', 'white', 'gray', 'navy', 'beige', 'tan', 'khaki', 'cream', 'brown']
        }
        
        # Initialize models
        self.top_model = None
        self.bottom_model = None
        self.footwear_model = None
        self.outerwear_model = None
        self.accessory_model = None
        
        # Initialize item embedding model for style similarity
        self.item_embedding_model = None
        self.kmeans_style_clusters = None
        
        # Load models if path is provided
        if models_path and os.path.exists(models_path):
            self._load_models(models_path)
        else:
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for each clothing category."""
        # These models will predict the suitability score for items given context
        self.top_model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.bottom_model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.footwear_model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.outerwear_model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.accessory_model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # Style similarity model
        self.item_embedding_model = NearestNeighbors(
            n_neighbors=5,
            algorithm='ball_tree',
            metric='cosine'
        )
        
        # Style clustering model
        self.kmeans_style_clusters = KMeans(
            n_clusters=10,
            random_state=42
        )
    
    def _load_models(self, models_path):
        """Load trained models from disk."""
        try:
            models = {
                'top_model': 'top_model.pkl',
                'bottom_model': 'bottom_model.pkl',
                'footwear_model': 'footwear_model.pkl',
                'outerwear_model': 'outerwear_model.pkl',
                'accessory_model': 'accessory_model.pkl',
                'item_embedding_model': 'item_embedding_model.pkl',
                'kmeans_style_clusters': 'kmeans_style_clusters.pkl'
            }
            
            for model_name, filename in models.items():
                model_path = os.path.join(models_path, filename)
                if os.path.exists(model_path):
                    setattr(self, model_name, joblib.load(model_path))
                else:
                    print(f"Model file {filename} not found. Initializing new model.")
                    self._initialize_models()
                    break
        except Exception as e:
            print(f"Error loading models: {e}")
            self._initialize_models()
    
    def _get_color_list(self) -> List[str]:
        """Return an expanded list of common clothing colors."""
        return [
            'red', 'blue', 'green', 'yellow', 'black', 'white', 'grey', 'gray',
            'purple', 'pink', 'orange', 'brown', 'navy', 'beige', 'cream', 'tan',
            'olive', 'burgundy', 'charcoal', 'silver', 'gold', 'teal', 'khaki',
            'maroon', 'mustard', 'coral', 'mint', 'turquoise', 'indigo', 'magenta',
            'lavender', 'peach', 'rust', 'emerald', 'ochre', 'crimson', 'azure',
            'lilac', 'amber', 'salmon', 'slate', 'mauve', 'taupe', 'cerulean',
            'ivory', 'camel', 'sage', 'periwinkle', 'plum', 'cobalt', 'fuchsia'
        ]
    
    def _get_material_list(self) -> List[str]:
        """Return an expanded list of common clothing materials."""
        return [
            'cotton', 'wool', 'leather', 'denim', 'silk', 'linen', 'polyester',
            'nylon', 'cashmere', 'velvet', 'suede', 'corduroy', 'fleece', 'tweed',
            'jersey', 'canvas', 'chino', 'flannel', 'chenille', 'satin', 'viscose',
            'spandex', 'rayon', 'acrylic', 'lyocell', 'mohair', 'merino', 'angora',
            'modal', 'twill', 'chambray', 'terry', 'mesh', 'sequin', 'bamboo',
            'microfiber', 'gabardine', 'herringbone', 'poplin', 'organza', 'taffeta',
            'fur', 'faux fur', 'sherpa', 'crepe', 'lamé', 'oxford', 'gore-tex'
        ]
    
    def _get_clothing_types(self) -> List[str]:
        """Return an expanded list of common clothing type categories."""
        return [
            # Tops
            't-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt', 'hoodie', 
            'polo', 'tank', 'turtleneck', 'tunic', 'button-down',
            'henley', 'crop top', 'camisole', 'pullover', 'jersey', 'long sleeve',
            'short sleeve', 'v-neck', 'crew neck', 'sleeveless', 'top',
            # Bottoms 
            'jeans', 'pants', 'trousers', 'shorts', 'skirt', 'chinos', 'leggings',
            'joggers', 'sweatpants', 'culottes', 'capris', 'jeggings', 'cargo',
            'khakis', 'slacks', 'dress pants', 'bermudas', 'palazzo', 'linen pants',
            # Dresses/One-pieces
            'dress', 'jumpsuit', 'romper', 'playsuit', 'gown', 'sundress', 'maxi',
            'midi', 'mini', 'shift', 'sheath', 'a-line', 'wrap', 'slip dress',
            # Outerwear
            'jacket', 'coat', 'blazer', 'parka', 'windbreaker', 'vest', 'cardigan',
            'trench', 'bomber', 'denim jacket', 'leather jacket', 'puffer', 'raincoat',
            'poncho', 'peacoat', 'overcoat', 'anorak', 'cape', 'shrug',
            # Footwear
            'shoes', 'boots', 'sneakers', 'sandals', 'loafers', 'flats', 'heels',
            'pumps', 'wedges', 'oxford shoes', 'slippers', 'mules', 'espadrilles',
            'mocassins', 'brogues', 'ankle boots', 'hiking boots', 'slip-ons',
            # Accessories
            'watch', 'scarf', 'tie', 'belt', 'hat', 'gloves', 'socks', 'necklace',
            'earrings', 'bracelet', 'ring', 'sunglasses', 'bag', 'purse', 'handbag',
            'wallet', 'backpack', 'tote', 'clutch', 'headband', 'beanie', 'cap',
            'beret', 'bowtie', 'pocket square', 'cufflinks', 'anklet', 'brooch'
        ]
    
    def _extract_features_from_description(self, description: str) -> Dict[str, Any]:
        """Extract comprehensive features from a clothing item description using advanced NLP."""
        doc = nlp(description.lower())
        
        # Extract colors with TFIDF weighting
        color_features = self.color_vectorizer.transform([description]).toarray()[0]
        # Get detected color names for later use
        color_indices = np.where(color_features > 0)[0]
        color_names = [self._get_color_list()[i] for i in color_indices]
        
        # Extract materials with TFIDF weighting
        material_features = self.material_vectorizer.transform([description]).toarray()[0]
        material_indices = np.where(material_features > 0)[0]
        material_names = [self._get_material_list()[i] for i in material_indices]
        
        # Extract clothing type
        type_features = self.type_vectorizer.transform([description]).toarray()[0]
        type_indices = np.where(type_features > 0)[0]
        type_names = [self._get_clothing_types()[i] for i in type_indices]
        
        # Named entity extraction
        entities = {ent.label_: ent.text for ent in doc.ents}
        
        # Extract descriptive adjectives
        descriptive_adjectives = [token.text for token in doc if token.pos_ == 'ADJ']
        
        # Determine category more robustly
        category = self._determine_category(description, type_features, type_names)
        
        # Calculate formality score (1-10 scale)
        formality = self._calculate_formality(description, doc, material_names, type_names)
        
        # Determine seasonality with higher precision
        seasonality = self._determine_seasonality(description, doc, material_names, type_names)
        
        # Extract pattern information
        pattern = self._extract_pattern(description)
        
        # Extract fit information
        fit = self._extract_fit(description)
        
        # Calculate style profile match
        style_profile = self._calculate_style_profile(description, descriptive_adjectives)
        
        # Calculate versatility score
        versatility = self._calculate_versatility(
            color_names, material_names, type_names, pattern, formality
        )
        
        # Build a richer feature vector for ML models
        numerical_features = np.concatenate([
            color_features, 
            material_features,
            type_features,
            [formality],
            [versatility],
            list(seasonality.values()),
        ])
        
        return {
            'description': description,
            'color_features': color_features,
            'color_names': color_names,
            'material_features': material_features,
            'material_names': material_names,
            'type_features': type_features,
            'type_names': type_names,
            'category': category,
            'formality': formality,
            'seasonality': seasonality,
            'pattern': pattern,
            'fit': fit,
            'style_profile': style_profile,
            'versatility': versatility,
            'numerical_features': numerical_features,
            'descriptive_adjectives': descriptive_adjectives
        }
    
    def _determine_category(self, description: str, type_features: np.ndarray, type_names: List[str]) -> str:
        """Enhanced category determination with better accuracy."""
        desc_lower = description.lower()
        
        # Define comprehensive category mappings
        category_mappings = {
            'top': [
                't-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt', 'hoodie', 'polo', 
                'tank', 'turtleneck', 'cardigan', 'tunic', 'button-down', 'henley', 
                'crop top', 'camisole', 'pullover', 'jersey', 'top'
            ],
            'bottom': [
                'jeans', 'pants', 'trousers', 'shorts', 'skirt', 'chinos', 'leggings',
                'joggers', 'sweatpants', 'culottes', 'capris', 'jeggings', 'cargo',
                'khakis', 'slacks', 'dress pants', 'bermudas', 'palazzo', 'linen pants'
            ],
            'one_piece': [
                'dress', 'jumpsuit', 'romper', 'playsuit', 'gown', 'sundress', 'maxi',
                'midi', 'mini', 'shift', 'sheath', 'a-line', 'wrap', 'slip dress'
            ],
            'outerwear': [
                'jacket', 'coat', 'blazer', 'parka', 'windbreaker', 'vest', 
                'trench', 'bomber', 'denim jacket', 'leather jacket', 'puffer', 'raincoat',
                'poncho', 'peacoat', 'overcoat', 'anorak', 'cape', 'shrug'
            ],
            'footwear': [
                'shoes', 'boots', 'sneakers', 'sandals', 'loafers', 'flats', 'heels',
                'pumps', 'wedges', 'oxford shoes', 'slippers', 'mules', 'espadrilles',
                'mocassins', 'brogues', 'ankle boots', 'hiking boots', 'slip-ons'
            ],
            'accessory': [
                'watch', 'scarf', 'tie', 'belt', 'hat', 'gloves', 'socks', 'necklace',
                'earrings', 'bracelet', 'ring', 'sunglasses', 'bag', 'purse', 'handbag',
                'wallet', 'backpack', 'tote', 'clutch', 'headband', 'beanie', 'cap',
                'beret', 'bowtie', 'pocket square', 'cufflinks', 'anklet', 'brooch'
            ]
        }
        
        # Check if any type names match a category
        for category, terms in category_mappings.items():
            if any(term in type_names for term in terms):
                # Special case for cardigans (can be top or outerwear)
                if 'cardigan' in type_names:
                    # If explicitly described as outerwear
                    if any(term in desc_lower for term in ['layer', 'jacket', 'coat', 'outerwear']):
                        return 'outerwear'
                    else:
                        return 'top'
                return category
        
        # If type names didn't help, check the full description
        for category, terms in category_mappings.items():
            if any(term in desc_lower for term in terms):
                return category
        
        # Last resort: use word frequencies and context to guess
        word_freq = Counter(desc_lower.split())
        for category, terms in category_mappings.items():
            for term in terms:
                if any(term in word for word in word_freq):
                    return category
                    
        return 'accessory'  # Default to accessory as it's the broadest category
    
    def _calculate_formality(self, description: str, doc: spacy.tokens.doc.Doc, 
                           materials: List[str], types: List[str]) -> float:
        """Calculate enhanced formality score (1-10) for a clothing item."""
        description = description.lower()
        formality_score = 5.0  # Default middle score
        
        # Materials influence on formality
        formal_materials = {
            'wool': 1.5, 'cashmere': 2.0, 'silk': 1.8, 'leather': 1.0, 
            'tweed': 1.5, 'linen': 0.8, 'velvet': 1.5, 'satin': 1.3
        }
        
        casual_materials = {
            'cotton': -0.8, 'denim': -1.5, 'fleece': -1.8, 'jersey': -1.3,
            'spandex': -1.2, 'polyester': -0.5, 'canvas': -1.0
        }
        
        # Adjust based on materials with weighted importance
        for material, weight in formal_materials.items():
            if material in materials:
                formality_score += weight
        
        for material, weight in casual_materials.items():
            if material in materials:
                formality_score += weight  # Weight is negative for casual materials
        
        # Clothing types influence on formality
        formal_types = {
            'suit': 3.0, 'blazer': 2.5, 'dress shirt': 2.0, 'oxford': 1.8,
            'loafers': 1.5, 'dress': 1.8, 'slacks': 1.5, 'coat': 1.0,
            'tie': 2.0, 'bow tie': 2.5, 'dress pants': 2.0, 'pumps': 1.8,
            'heels': 1.5, 'gown': 3.0, 'tuxedo': 4.0
        }
        
        casual_types = {
            't-shirt': -1.5, 'hoodie': -2.0, 'sweatshirt': -1.8, 'jeans': -1.5,
            'sneakers': -1.5, 'shorts': -2.0, 'flip-flops': -2.5, 'tank': -1.3,
            'sandals': -1.0, 'sweatpants': -2.5, 'joggers': -2.0, 'beanie': -1.0
        }
        
        # Check types in both the extracted types and full description
        for type_name, weight in formal_types.items():
            if type_name in types or type_name in description:
                formality_score += weight
        
        for type_name, weight in casual_types.items():
            if type_name in types or type_name in description:
                formality_score += weight  # Weight is negative for casual types
        
        # Check for explicit formality/casualness descriptors
        formality_descriptors = {
            'formal': 2.0, 'business': 1.8, 'professional': 1.5, 'elegant': 1.8,
            'sophisticated': 1.5, 'dressy': 1.3, 'upscale': 1.8, 'evening': 1.5,
            'fancy': 1.3, 'polished': 1.0, 'refined': 1.3, 'smart': 1.0
        }
        
        casual_descriptors = {
            'casual': -1.5, 'relaxed': -1.3, 'everyday': -1.0, 'laid-back': -1.5,
            'comfortable': -0.8, 'cozy': -1.0, 'slouchy': -1.5, 'distressed': -1.3,
            'worn-in': -1.0, 'sporty': -1.2, 'athleisure': -1.5, 'lounge': -1.8
        }
        
        # Check descriptors in the full description
        for desc, weight in formality_descriptors.items():
            if desc in description:
                formality_score += weight
        
        for desc, weight in casual_descriptors.items():
            if desc in description:
                formality_score += weight  # Weight is negative for casual descriptors
        
        # Additional context clues from adjectives
        adjectives = [token.text for token in doc if token.pos_ == 'ADJ']
        formal_adj = ['tailored', 'structured', 'pressed', 'starched', 'crisp']
        casual_adj = ['baggy', 'loose', 'comfortable', 'oversized', 'distressed']
        
        for adj in formal_adj:
            if adj in adjectives or adj in description:
                formality_score += 0.5
                
        for adj in casual_adj:
            if adj in adjectives or adj in description:
                formality_score -= 0.5
        
        # Ensure score stays within 1-10 range
        return max(1, min(10, formality_score))
    
    def _determine_seasonality(self, description: str, doc: spacy.tokens.doc.Doc, 
                             materials: List[str], types: List[str]) -> Dict[str, float]:
        """Determine seasonality scores with higher precision."""
        desc_lower = description.lower()
        seasonality = {
            'spring': 0.25,  # Default values
            'summer': 0.25,
            'fall': 0.25,
            'winter': 0.25
        }
        
        # Material-based seasonality adjustments
        summer_materials = ['linen', 'cotton', 'chambray', 'mesh', 'chiffon', 'rayon']
        winter_materials = ['wool', 'cashmere', 'flannel', 'velvet', 'fleece', 'sherpa', 'fur', 'suede']
        spring_materials = ['cotton', 'linen', 'light wool', 'poplin', 'silk']
        fall_materials = ['corduroy', 'tweed', 'leather', 'denim', 'suede', 'flannel']
        
        # Adjust based on materials
        for material in materials:
            if material in summer_materials:
                seasonality['summer'] += 0.15
                seasonality['winter'] -= 0.1
            if material in winter_materials:
                seasonality['winter'] += 0.15
                seasonality['summer'] -= 0.1
            if material in spring_materials:
                seasonality['spring'] += 0.1
            if material in fall_materials:
                seasonality['fall'] += 0.1
        
        # Clothing types and characteristics
        summer_items = ['shorts', 'sandals', 'tank', 'sleeveless', 'short sleeve', 'sundress', 'swimwear']
        winter_items = ['sweater', 'coat', 'boots', 'gloves', 'scarf', 'parka', 'beanie', 'turtleneck']
        spring_items = ['light jacket', 'cardigan', 'rain jacket', 'windbreaker', 'loafers', 'flats']
        fall_items = ['jacket', 'light sweater', 'blazer', 'hoodie', 'ankle boots', 'vest']
        
        # Check for seasonal types
        for item in summer_items:
            if item in desc_lower:
                seasonality['summer'] += 0.2
                seasonality['winter'] -= 0.15
        
        for item in winter_items:
            if item in desc_lower:
                seasonality['winter'] += 0.2
                seasonality['summer'] -= 0.15
        
        for item in spring_items:
            if item in desc_lower:
                seasonality['spring'] += 0.15
        
        for item in fall_items:
            if item in desc_lower:
                seasonality['fall'] += 0.15
        
        # Descriptor-based adjustments
        summer_descriptors = ['lightweight', 'breathable', 'cooling', 'airy', 'tropical']
        winter_descriptors = ['warm', 'insulated', 'heavy', 'thick', 'cozy', 'thermal', 'heated']
        spring_descriptors = ['light', 'pastel', 'floral', 'bright', 'rain-resistant']
        fall_descriptors = ['layering', 'earth tone', 'rich', 'mid-weight', 'rust']
        
        # Check descriptors
        for desc in summer_descriptors:
            if desc in desc_lower:
                seasonality['summer'] += 0.15
                seasonality['winter'] -= 0.1
        
        for desc in winter_descriptors:
            if desc in desc_lower:
                seasonality['winter'] += 0.15
                seasonality['summer'] -= 0.1
        
        for desc in spring_descriptors:
            if desc in desc_lower:
                seasonality['spring'] += 0.1
        
        for desc in fall_descriptors:
            if desc in desc_lower:
                seasonality['fall'] += 0.1
        
        # Explicit season mentions
        for season in seasonality.keys():
            if season in desc_lower:
                seasonality[season] += 0.3
        
        # Color influences on seasonality
        color_seasonality = {
            'spring': ['pastel', 'mint', 'peach', 'pink', 'light blue', 'yellow', 'lavender'],
            'summer': ['bright', 'neon', 'coral', 'turquoise', 'white', 'yellow', 'hot pink', 'aqua'],
            'fall': ['burgundy', 'mustard', 'olive', 'rust', 'brown', 'orange', 'forest green', 'mauve'],
            'winter': ['black', 'navy', 'dark green', 'burgundy', 'charcoal', 'silver', 'white', 'red']
        }
        
        # Check for seasonal colors
        for season, colors in color_seasonality.items():
            for color in colors:
                if color in desc_lower:
                    seasonality[season] += 0.08
        
        # Normalize to ensure they sum to 1
        total = sum(seasonality.values())
        for season in seasonality:
            seasonality[season] = max(0.05, seasonality[season] / total)  # Ensure minimum 0.05
        return seasonality

    def _extract_pattern(self, description: str) -> str:
        """Extract pattern information from a clothing description."""
        description = description.lower()
        
        patterns = {
            'solid': ['solid', 'plain', 'basic', 'single color', 'one color'],
            'striped': ['stripe', 'striped', 'stripes', 'pinstripe', 'vertical stripe', 'horizontal stripe'],
            'plaid': ['plaid', 'tartan', 'check', 'checked', 'checkered', 'gingham'],
            'floral': ['floral', 'flower', 'flowers', 'botanical', 'rose', 'daisy'],
            'polka dot': ['polka dot', 'polka-dot', 'dots', 'spotted', 'dot pattern'],
            'animal print': ['animal print', 'leopard', 'zebra', 'cheetah', 'snake', 'python', 'crocodile', 'tiger'],
            'geometric': ['geometric', 'triangle', 'square', 'diamond pattern', 'hexagon', 'chevron', 'zigzag'],
            'print': ['print', 'pattern', 'graphic', 'design', 'logo', 'motif'],
            'colorblock': ['colorblock', 'color-block', 'color block', 'two-tone', 'two tone']
        }
        
        for pattern_name, keywords in patterns.items():
            if any(keyword in description for keyword in keywords):
                return pattern_name
                
        # Default to solid if no pattern is detected
        return 'solid'
    
    def _extract_fit(self, description: str) -> str:
        """Extract fit information from a clothing description."""
        description = description.lower()
        
        fits = {
            'slim': ['slim', 'fitted', 'tailored', 'skinny', 'tight', 'form-fitting', 'narrow'],
            'regular': ['regular', 'classic', 'standard', 'straight', 'normal'],
            'loose': ['loose', 'relaxed', 'oversized', 'baggy', 'wide', 'boxy', 'roomy'],
            'stretchy': ['stretchy', 'stretch', 'flexible', 'elastic', 'spandex']
        }
        
        for fit_name, keywords in fits.items():
            if any(keyword in description for keyword in keywords):
                return fit_name
                
        # Default to regular fit if no specific fit is detected
        return 'regular'
    
    def _calculate_style_profile(self, description: str, adjectives: List[str]) -> Dict[str, float]:
        """Calculate how well an item matches different style profiles."""
        desc_lower = description.lower()
        
        # Initialize style scores
        style_scores = {style: 0.0 for style in self.style_profiles.keys()}
        
        # Calculate match based on keyword presence
        for style, keywords in self.style_profiles.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    style_scores[style] += 1.0
        
        # Consider adjectives that aren't explicitly in style keywords
        style_adj_mapping = {
            'casual': ['easy', 'simple', 'everyday', 'versatile'],
            'formal': ['structured', 'elegant', 'refined', 'luxurious'],
            'business': ['sharp', 'pressed', 'crisp', 'proper'],
            'sporty': ['functional', 'practical', 'technical', 'breathable'],
            'bohemian': ['flowy', 'relaxed', 'natural', 'earthy'],
            'vintage': ['classic', 'timeless', 'nostalgic', 'traditional'],
            'preppy': ['smart', 'neat', 'clean', 'fresh'],
            'streetwear': ['bold', 'edgy', 'graphic', 'statement'],
            'minimalist': ['sleek', 'modern', 'streamlined', 'essential']
        }
        
        for adj in adjectives:
            for style, related_adj in style_adj_mapping.items():
                if adj in related_adj:
                    style_scores[style] += 0.5
        
        # Normalize scores (if any matches found)
        total_score = sum(style_scores.values())
        if total_score > 0:
            for style in style_scores:
                style_scores[style] /= total_score
        else:
            # Default to equal probability across all styles
            for style in style_scores:
                style_scores[style] = 1.0 / len(style_scores)
        
        return style_scores
    
    def _calculate_versatility(self, colors: List[str], materials: List[str], 
                             types: List[str], pattern: str, formality: float) -> float:
        """Calculate a versatility score (0-10) for an item."""
        versatility_score = 5.0  # Start with middle score
        
        # Neutral colors are more versatile
        neutral_colors = ['black', 'white', 'gray', 'navy', 'beige', 'cream', 'tan', 'khaki', 'brown']
        if any(color in neutral_colors for color in colors):
            versatility_score += 2.0
        
        # Vibrant colors are less versatile
        vibrant_colors = ['neon', 'bright', 'hot pink', 'electric blue', 'lime green']
        if any(vibrant in ' '.join(colors) for vibrant in vibrant_colors):
            versatility_score -= 1.5
        
        # Solid patterns are more versatile than busy patterns
        if pattern == 'solid':
            versatility_score += 1.5
        elif pattern in ['floral', 'animal print', 'geometric']:
            versatility_score -= 1.0
        
        # Basic types are more versatile
        basic_types = ['t-shirt', 'shirt', 'jeans', 'pants', 'sweater', 'blazer']
        if any(basic in types for basic in basic_types):
            versatility_score += 1.0
        
        # Items in the mid-range of formality are more versatile
        if 4 <= formality <= 7:
            versatility_score += 1.5
        elif formality < 3 or formality > 8:
            versatility_score -= 1.0
        
        # Durable, easy-care materials are more versatile
        versatile_materials = ['cotton', 'denim', 'polyester', 'wool']
        if any(material in versatile_materials for material in materials):
            versatility_score += 1.0
        
        # Delicate materials are less versatile
        delicate_materials = ['silk', 'cashmere', 'suede', 'velvet']
        if any(material in delicate_materials for material in materials):
            versatility_score -= 1.0
        
        # Ensure score stays within 0-10 range
        return max(0, min(10, versatility_score))
    
    def _calculate_color_coordination(self, item1_colors: List[str], item2_colors: List[str]) -> float:
        """Calculate how well two items' colors coordinate (0-1 score)."""
        # If either item has no color data, default to neutral coordination
        if not item1_colors or not item2_colors:
            return 0.5
        
        coordination_score = 0.0
        
        # Check for direct color matches (monochromatic)
        for color1 in item1_colors:
            if color1 in item2_colors:
                coordination_score += 0.8
                break
        
        # Check for complementary color pairs
        for color1 in item1_colors:
            if color1 in self.color_coordination['complementary']:
                complementary_colors = self.color_coordination['complementary'][color1]
                if any(color2 in complementary_colors for color2 in item2_colors):
                    coordination_score += 0.9
                    break
        
        # Neutral colors go with anything
        neutral_base = self.color_coordination['neutral_base']
        if any(color in neutral_base for color in item1_colors) or any(color in neutral_base for color in item2_colors):
            coordination_score += 0.7
        
        # Check for monochromatic combinations (variations of the same color family)
        for color_family in self.color_coordination['monochromatic']:
            if (any(color in self.color_coordination['monochromatic'][color_family] for color in item1_colors) and
                any(color in self.color_coordination['monochromatic'][color_family] for color in item2_colors)):
                coordination_score += 0.8
                break
        
        # Normalize score to 0-1 range
        return min(1.0, coordination_score)
    
    def _predict_item_score(self, item_features, occasion_features, weather_categories, style_preferences):
        """Use ML models to predict item suitability score based on context."""
        category = item_features['category']
        
        # Handle one-piece items (e.g., dresses) as a special case
        if category == 'one_piece':
            # Treat one-piece items as both top and bottom for scoring
            category = 'top'  # Default to scoring as a top
        
        # Prepare features for prediction
        # Combine item features with context features
        context_vector = np.concatenate([
            list(occasion_features.values()),
            list(weather_categories.values())
        ])
        
        # Get the appropriate model for this category
        model = getattr(self, f"{category}_model")
        
        if model and hasattr(model, 'predict'):
            # If we have a trained model, use it
            features = np.concatenate([
                item_features['numerical_features'],
                context_vector
            ])
            
            # Handle style preferences if provided
            if style_preferences and item_features['style_profile']:
                style_match_score = 0
                user_styles = style_preferences.lower().split()
                for style, score in item_features['style_profile'].items():
                    if any(user_style in style for user_style in user_styles):
                        style_match_score += score
                
                features = np.append(features, [style_match_score])
                
            # Reshape for single sample prediction
            features = features.reshape(1, -1)
            
            try:
                # Predict suitability score
                score = model.predict(features)[0]
                return score
            except Exception as e:
                # If prediction fails, fall back to rule-based scoring
                print(f"Model prediction failed: {e}")
                return self._calculate_rule_based_score(item_features, occasion_features, weather_categories)
        else:
            # If no model is available, use rule-based scoring
            return self._calculate_rule_based_score(item_features, occasion_features, weather_categories)
    
    def _calculate_rule_based_score(self, item_features, occasion_features, weather_categories):
        """Calculate item suitability using rule-based approach when ML model is unavailable."""
        # Calculate weather appropriateness
        weather_score = self._calculate_weather_appropriateness(item_features, weather_categories)
        
        # Calculate formality match
        formality_score = self._calculate_formality_match(
            item_features['formality'], 
            occasion_features['formality']
        )
        
        # Calculate versatility bonus
        versatility_bonus = item_features['versatility'] / 20  # Scale 0-10 to 0-0.5
        
        # Combine scores with weighted importance
        overall_score = (
            weather_score * 0.4 + 
            formality_score * 0.5 + 
            versatility_bonus
        )
        
        return overall_score
    
    def _categorize_weather(self, weather_description: str, temperature: float) -> Dict[str, float]:
        """Enhanced categorization of weather into different types with probabilities."""
        weather_desc_lower = weather_description.lower()
        
        # Initialize scores for each weather category
        weather_scores = {category: 0.0 for category in self.weather_categories}
        
        # Score based on weather description with weighted keywords
        for category, keywords in self.weather_categories.items():
            for keyword in keywords:
                if keyword in weather_desc_lower:
                    # Primary keywords have higher weight
                    weight = 0.8 if keyword in keywords[:3] else 0.5
                    weather_scores[category] += weight
        
        # Score based on temperature with more nuanced ranges
        if temperature > 30:  # Very hot
            weather_scores['hot'] += 1.0
            weather_scores['cold'] = 0
        elif temperature > 25:  # Hot
            weather_scores['hot'] += 0.8
            weather_scores['mild'] += 0.2
            weather_scores['cold'] = 0
        elif temperature > 20:  # Warm
            weather_scores['hot'] += 0.5
            weather_scores['mild'] += 0.5
            weather_scores['cold'] = 0
        elif temperature > 15:  # Mild
            weather_scores['mild'] += 0.8
            weather_scores['hot'] += 0.2
            weather_scores['cold'] += 0.1
        elif temperature > 10:  # Cool
            weather_scores['mild'] += 0.6
            weather_scores['cold'] += 0.4
        elif temperature > 5:  # Cold
            weather_scores['cold'] += 0.7
            weather_scores['mild'] += 0.3
            weather_scores['hot'] = 0
        elif temperature > 0:  # Very cold
            weather_scores['cold'] += 0.9
            weather_scores['mild'] += 0.1
            weather_scores['hot'] = 0
        else:  # Freezing
            weather_scores['cold'] += 1.0
            weather_scores['mild'] = 0
            weather_scores['hot'] = 0
        
        # Special case for precipitation
        precipitation_terms = ['rain', 'snow', 'drizzle', 'shower', 'precipitation', 'wet', 'damp', 'thunderstorm']
        if any(term in weather_desc_lower for term in precipitation_terms):
            weather_scores['wet'] += 0.8
            
            # Snow is cold and wet
            if 'snow' in weather_desc_lower:
                weather_scores['cold'] += 0.5
        
        # Special case for wind
        wind_terms = ['wind', 'breezy', 'gusty', 'blustery', 'gale', 'drafty']
        if any(term in weather_desc_lower for term in wind_terms):
            weather_scores['windy'] += 0.8
            
            # Wind chill makes it feel colder
            if temperature < 15:
                weather_scores['cold'] += 0.3
        
        # Ensure minimum score of 0
        for category in weather_scores:
            weather_scores[category] = max(0, weather_scores[category])
        
        # Normalize
        total_score = sum(weather_scores.values())
        if total_score > 0:
            for category in weather_scores:
                weather_scores[category] /= total_score
        else:
            # Default to mild if no strong signals
            weather_scores['mild'] = 1.0
        
        return weather_scores
    
    def _calculate_occasion_score(self, occasion: str) -> Dict[str, float]:
        """Calculate comprehensive occasion characteristics."""
        occasion_lower = occasion.lower()
        
        # Default scores
        occasion_scores = {
            'formality': 5.0,
            'social': 0.5,
            'professional': 0.5,
            'active': 0.3,
            'outdoor': 0.5,
            'evening': 0.5
        }
        
        # Formality based on occasion keywords
        for occ, score in self.occasion_formality.items():
            if occ in occasion_lower:
                occasion_scores['formality'] = score
                break
        
        # Social vs professional context
        social_terms = ['party', 'date', 'wedding', 'dinner', 'celebration', 'brunch', 'cocktail', 'reception']
        professional_terms = ['work', 'office', 'business', 'interview', 'meeting', 'conference', 'presentation']
        
        if any(term in occasion_lower for term in social_terms):
            occasion_scores['social'] = 0.8
            occasion_scores['professional'] = 0.2
            
        if any(term in occasion_lower for term in professional_terms):
            occasion_scores['professional'] = 0.8
            occasion_scores['social'] = 0.2
        
        # Active vs passive
        active_terms = ['sports', 'workout', 'gym', 'exercise', 'hiking', 'outdoor', 'activity']
        if any(term in occasion_lower for term in active_terms):
            occasion_scores['active'] = 0.8
        
        # Indoor vs outdoor
        outdoor_terms = ['outdoor', 'outside', 'park', 'garden', 'beach', 'hiking', 'picnic']
        if any(term in occasion_lower for term in outdoor_terms):
            occasion_scores['outdoor'] = 0.8
        
        # Time of day
        evening_terms = ['evening', 'night', 'dinner', 'cocktail', 'party', 'formal']
        if any(term in occasion_lower for term in evening_terms):
            occasion_scores['evening'] = 0.8
        
        return occasion_scores
    
    def _calculate_weather_appropriateness(self, item_features: Dict[str, Any], 
                                         weather_categories: Dict[str, float]) -> float:
        """Calculate how appropriate an item is for the current weather with enhanced precision."""
        seasonality = item_features['seasonality']
        
        # Map weather categories to seasons more precisely
        weather_season_map = {
            'hot': {'summer': 0.8, 'spring': 0.2},
            'cold': {'winter': 0.8, 'fall': 0.2},
            'wet': {'fall': 0.4, 'spring': 0.4, 'winter': 0.2},
            'windy': {'fall': 0.5, 'spring': 0.3, 'winter': 0.2},
            'mild': {'spring': 0.5, 'fall': 0.3, 'summer': 0.2}
        }
        
        # Material appropriateness for weather
        material_weather_suitability = {
            'hot': {
                'good': ['cotton', 'linen', 'silk', 'rayon', 'chambray'],
                'bad': ['wool', 'leather', 'fleece', 'velvet', 'cashmere']
            },
            'cold': {
                'good': ['wool', 'cashmere', 'fleece', 'leather', 'down', 'fur', 'sherpa'],
                'bad': ['linen', 'silk', 'mesh', 'chiffon']
            },
            'wet': {
                'good': ['polyester', 'nylon', 'gore-tex', 'vinyl', 'leather', 'wool'],
                'bad': ['suede', 'silk', 'cotton', 'velvet']
            },
            'windy': {
                'good': ['leather', 'denim', 'wool', 'polyester', 'nylon'],
                'bad': ['silk', 'light cotton', 'chiffon', 'loose weave']
            }
        }
        
        # Calculate appropriateness score
        weather_score = 0.0
        material_score = 0.5  # Default neutral score
        
        # Season-based score
        for weather_cat, weight in weather_categories.items():
            if weather_cat in weather_season_map:
                for season, season_weight in weather_season_map[weather_cat].items():
                    weather_score += weight * season_weight * seasonality[season]
        
        # Material-based score
        for weather_cat, weight in weather_categories.items():
            if weather_cat in material_weather_suitability:
                good_materials = material_weather_suitability[weather_cat]['good']
                bad_materials = material_weather_suitability[weather_cat]['bad']
                
                if any(material in good_materials for material in item_features['material_names']):
                    material_score += weight * 0.3
                if any(material in bad_materials for material in item_features['material_names']):
                    material_score -= weight * 0.3
        
        # Pattern and type consideration for weather
        if weather_categories.get('wet', 0) > 0.5:
            # Patterns that show water stains less
            if item_features['pattern'] in ['dark', 'patterned', 'print', 'plaid']:
                weather_score += 0.1
            # Footwear that's good for wet weather
            if item_features['category'] == 'footwear' and any(term in ' '.join(item_features['type_names']) 
                                                            for term in ['boots', 'waterproof', 'water-resistant']):
                weather_score += 0.2
        
        # Combine scores (with more weight on seasonality than materials)
        combined_score = weather_score * 0.7 + material_score * 0.3
        
        # Normalize to 0-1 range
        return min(1.0, max(0.0, combined_score))
    
    def _calculate_formality_match(self, item_formality: float, occasion_formality: float) -> float:
        """Calculate how well an item's formality matches the occasion requirements."""
        # Calculate base difference
        diff = abs(item_formality - occasion_formality)
        
        # Penalty for being underdressed is higher than for being overdressed
        if item_formality < occasion_formality:
            # Being underdressed is worse than being overdressed
            penalty = 1.5 * diff
        else:
            # Overdressing penalty
            penalty = 0.8 * diff
            
            # Less penalty for slightly overdressing
            if diff < 2:
                penalty *= 0.8
        
        # Additional penalty for extreme mismatches
        if diff > 5:
            penalty *= 1.5
        
        # Convert to a 0-1 score (higher is better)
        score = max(0, 1 - (penalty / 10))
        
        # Bonus for perfect match
        if diff < 0.5:
            score = min(1.0, score + 0.2)
            
        return score

    def _find_complementary_items(self, selected_item, all_items, category):
        """Find items that complement the selected item in terms of style and color."""
        complementary_items = []
        
        for item in all_items:
            if item['category'] == category:
                # Calculate color coordination score
                color_score = self._calculate_color_coordination(
                    selected_item['color_names'], 
                    item['color_names']
                )
                
                # Get style compatibility
                style_match = 0.5  # Default medium compatibility
                for style, score in selected_item['style_profile'].items():
                    if score > 0.3:  # If this is a prominent style in the first item
                        # Check if second item has similar style score
                        if style in item['style_profile'] and item['style_profile'][style] > 0.3:
                            style_match += 0.3
                
                # Calculate overall coordination score
                coordination_score = color_score * 0.6 + style_match * 0.4
                
                # Add to complementary items with score
                complementary_items.append((item, coordination_score))
        
        # Sort by coordination score (descending)
        complementary_items.sort(key=lambda x: x[1], reverse=True)
        
        return complementary_items
    
    def process_clothing_items(self, clothing_descriptions: List[str]) -> pd.DataFrame:
        """Process clothing descriptions into a feature dataframe with enhanced features."""
        items_features = []
        
        for description in clothing_descriptions:
            features = self._extract_features_from_description(description)
            items_features.append(features)
        
        return pd.DataFrame(items_features)
    
    def suggest_outfit(self, clothing_descriptions: List[str], occasion: str, 
                      weather_description: str, temperature: float) -> Dict[str, str]:
        """Suggest an outfit based on occasion and weather."""
        # Process clothing items
        clothing_df = self.process_clothing_items(clothing_descriptions)
        
        # Categorize weather with enhanced precision
        weather_categories = self._categorize_weather(weather_description, temperature)
        
        # Calculate occasion characteristics
        occasion_features = self._calculate_occasion_score(occasion)
        
        # Prepare to track item features for coordination
        selected_items_features = {}
        
        # Calculate scores for each item using enhanced ML approach
        clothing_df['weather_score'] = clothing_df.apply(
            lambda row: self._calculate_weather_appropriateness(row, weather_categories), axis=1
        )
        
        clothing_df['formality_score'] = clothing_df.apply(
            lambda row: self._calculate_formality_match(row['formality'], occasion_features['formality']), axis=1
        )
        
        # Calculate overall score (combine weather and formality scores)
        clothing_df['overall_score'] = (clothing_df['weather_score'] * 0.4 + 
                                      clothing_df['formality_score'] * 0.6)
        
        # Sort by overall score within each category
        clothing_df = clothing_df.sort_values(['category', 'overall_score'], ascending=[True, False])
        
        # Select the best item from each required category
        outfit = {}
        required_categories = ['top', 'bottom', 'footwear']
        optional_categories = ['outerwear', 'accessory']
        
        # First, handle one-piece items (dresses, jumpsuits) specially
        one_piece_items = clothing_df[clothing_df['category'] == 'one_piece']
        if not one_piece_items.empty and one_piece_items.iloc[0]['overall_score'] > 0.7:
            # If we have a good one-piece item, use it instead of separate top and bottom
            outfit['one_piece'] = one_piece_items.iloc[0]['description']
            selected_items_features['one_piece'] = one_piece_items.iloc[0].to_dict()
            
            # Remove top and bottom from required categories
            required_categories = [cat for cat in required_categories if cat not in ['top', 'bottom']]
        
        # Next, select required items
        for category in required_categories:
            category_items = clothing_df[clothing_df['category'] == category]
            if not category_items.empty:
                best_item = category_items.iloc[0]
                outfit[category] = best_item['description']
                selected_items_features[category] = best_item.to_dict()
            else:
                outfit[category] = f"No suitable {category} found"
        
        # Then, select optional items if they have good scores
        for category in optional_categories:
            category_items = clothing_df[clothing_df['category'] == category]
            if not category_items.empty and category_items.iloc[0]['overall_score'] > 0.6:
                # For outerwear, check if temperature actually warrants it
                if category == 'outerwear':
                    if temperature < 20 or weather_categories.get('wet', 0) > 0.4 or weather_categories.get('windy', 0) > 0.4:
                        outfit[category] = category_items.iloc[0]['description']
                        selected_items_features[category] = category_items.iloc[0].to_dict()
                else:
                    outfit[category] = category_items.iloc[0]['description']
                    selected_items_features[category] = category_items.iloc[0].to_dict()
        
        return outfit

    def format_outfit_suggestion(self, outfit: Dict[str, str]) -> str:
        """Format the outfit suggestion as bullet points with additional context."""
        result = []
        
        # Order categories for output
        categories_order = ['one_piece', 'top', 'bottom', 'outerwear', 'footwear', 'accessory']
        
        # Add header
        result.append("Suggested Outfit:")
        
        for category in categories_order:
            if category in outfit:
                # Capitalize first letter of category
                category_name = category[0].upper() + category[1:]
                
                # Handle one_piece differently
                if category == 'one_piece':
                    category_name = "Dress/Jumpsuit"
                
                result.append(f"• {category_name}: {outfit[category]}")
        
        return "\n".join(result)

def get_outfit_suggestion(clothing_descriptions: str, occasion: str, age: int, style_preferences: str,
                         location: str, weather: dict) -> str:
    """
    Use ML approach to generate an outfit suggestion based on clothing items,
    occasion, and weather data.
    """
    # Parse clothing descriptions into a list
    clothing_items = [desc.strip() for desc in clothing_descriptions.split('\n') if desc.strip()]
    
    # Extract descriptions without the leading "- "
    cleaned_items = [item[2:] if item.startswith('- ') else item for item in clothing_items]
    
    # Initialize outfit suggester
    suggester = OutfitSuggester()
    
    # Generate outfit
    outfit = suggester.suggest_outfit(
        clothing_descriptions=cleaned_items,
        occasion=occasion,
        weather_description=weather['description'],
        temperature=weather['temperature']
    )
    
    # Format the result
    outfit_suggestion = suggester.format_outfit_suggestion(outfit)
    
    return outfit_suggestion
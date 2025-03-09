import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import OneHotEncoder
import spacy
import re
from typing import List, Dict, Any, Tuple

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
    def __init__(self):
        # Initialize feature extractors
        self.color_vectorizer = CountVectorizer(vocabulary=self._get_color_list())
        self.material_vectorizer = CountVectorizer(vocabulary=self._get_material_list())
        self.type_vectorizer = CountVectorizer(vocabulary=self._get_clothing_types())
        
        # Weather categories
        self.weather_categories = {
            'hot': ['sunny', 'hot', 'warm', 'clear'],
            'cold': ['cold', 'freezing', 'chilly', 'snow', 'icy'],
            'wet': ['rain', 'rainy', 'shower', 'drizzle', 'thunderstorm'],
            'windy': ['windy', 'breezy', 'gusty'],
            'mild': ['mild', 'pleasant', 'partly cloudy', 'cloudy']
        }
        
        # Occasion formality scores (1-10)
        self.occasion_formality = {
            'casual': 1,
            'everyday': 2, 
            'work': 5,
            'office': 6,
            'business': 7,
            'date': 6,
            'party': 5,
            'formal': 8,
            'wedding': 9,
            'interview': 8
        }
        
        # Initialize models
        self.top_model = None
        self.bottom_model = None
        self.footwear_model = None
        self.outerwear_model = None
        self.accessory_model = None
        
    def _get_color_list(self) -> List[str]:
        """Return a list of common clothing colors."""
        return [
            'red', 'blue', 'green', 'yellow', 'black', 'white', 'grey', 'gray',
            'purple', 'pink', 'orange', 'brown', 'navy', 'beige', 'cream', 'tan',
            'olive', 'burgundy', 'charcoal', 'silver', 'gold', 'teal', 'khaki'
        ]
    
    def _get_material_list(self) -> List[str]:
        """Return a list of common clothing materials."""
        return [
            'cotton', 'wool', 'leather', 'denim', 'silk', 'linen', 'polyester',
            'nylon', 'cashmere', 'velvet', 'suede', 'corduroy', 'fleece', 'tweed'
        ]
    
    def _get_clothing_types(self) -> List[str]:
        """Return a list of common clothing type categories."""
        return [
            # Tops
            't-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt', 'hoodie', 
            'polo', 'tank', 'turtleneck', 'cardigan',
            # Bottoms 
            'jeans', 'pants', 'trousers', 'shorts', 'skirt', 'chinos',
            # Outerwear
            'jacket', 'coat', 'blazer', 'parka', 'windbreaker', 'vest',
            # Footwear
            'shoes', 'boots', 'sneakers', 'sandals', 'loafers',
            # Accessories
            'watch', 'scarf', 'tie', 'belt', 'hat', 'gloves', 'socks'
        ]
    
    def _extract_features_from_description(self, description: str) -> Dict[str, Any]:
        """Extract features from a clothing item description."""
        doc = nlp(description.lower())
        
        # Extract colors
        color_features = self.color_vectorizer.transform([description]).toarray()[0]
        
        # Extract materials
        material_features = self.material_vectorizer.transform([description]).toarray()[0]
        
        # Extract clothing type
        type_features = self.type_vectorizer.transform([description]).toarray()[0]
        
        # Determine category
        category = self._determine_category(description, type_features)
        
        # Calculate formality score (1-10 scale)
        formality = self._calculate_formality(description, doc)
        
        # Determine seasonality
        seasonality = self._determine_seasonality(description, doc)
        
        return {
            'description': description,
            'color_features': color_features,
            'material_features': material_features,
            'type_features': type_features,
            'category': category,
            'formality': formality,
            'seasonality': seasonality
        }
    
    def _determine_category(self, description: str, type_features: np.ndarray) -> str:
        """Determine the category of a clothing item based on its description and type features."""
        type_indices = np.where(type_features == 1)[0]
        type_names = [self._get_clothing_types()[i] for i in type_indices]
        
        # Simple category determination
        if any(t in ['t-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt', 
                   'hoodie', 'polo', 'tank', 'turtleneck', 'cardigan'] for t in type_names):
            return 'top'
        elif any(t in ['jeans', 'pants', 'trousers', 'shorts', 'skirt', 'chinos'] for t in type_names):
            return 'bottom'
        elif any(t in ['jacket', 'coat', 'blazer', 'parka', 'windbreaker', 'vest'] for t in type_names):
            return 'outerwear'
        elif any(t in ['shoes', 'boots', 'sneakers', 'sandals', 'loafers'] for t in type_names):
            return 'footwear'
        elif any(t in ['watch', 'scarf', 'tie', 'belt', 'hat', 'gloves', 'socks'] for t in type_names):
            return 'accessory'
        else:
            # Try to determine category from full description
            desc_lower = description.lower()
            if any(word in desc_lower for word in ['t-shirt', 'shirt', 'blouse', 'sweater', 'sweatshirt']):
                return 'top'
            elif any(word in desc_lower for word in ['jeans', 'pants', 'trousers', 'shorts', 'skirt']):
                return 'bottom'
            elif any(word in desc_lower for word in ['jacket', 'coat', 'blazer']):
                return 'outerwear'
            elif any(word in desc_lower for word in ['shoes', 'boots', 'sneakers']):
                return 'footwear'
            else:
                return 'accessory'  # Default to accessory
    
    def _calculate_formality(self, description: str, doc: spacy.tokens.doc.Doc) -> float:
        """Calculate formality score (1-10) for a clothing item."""
        description = description.lower()
        formality_score = 5.0  # Default middle score
        
        # Materials that influence formality
        formal_materials = ['wool', 'cashmere', 'silk', 'leather']
        casual_materials = ['cotton', 'denim', 'fleece']
        
        # Adjust based on materials
        for material in formal_materials:
            if material in description:
                formality_score += 1
        
        for material in casual_materials:
            if material in description:
                formality_score -= 1
        
        # Adjust based on clothing types
        if re.search(r'\b(t-shirt|hoodie|sweatshirt|jeans|sneakers)\b', description):
            formality_score -= 1.5
        
        if re.search(r'\b(oxford|dress shirt|slacks|suit|blazer|loafers)\b', description):
            formality_score += 1.5
        
        if re.search(r'\b(formal|business|professional)\b', description):
            formality_score += 2
        
        if re.search(r'\b(casual|relaxed|everyday)\b', description):
            formality_score -= 2
        
        # Ensure score stays within 1-10 range
        return max(1, min(10, formality_score))
    
    def _determine_seasonality(self, description: str, doc: spacy.tokens.doc.Doc) -> Dict[str, float]:
        """Determine seasonality scores for a clothing item."""
        desc_lower = description.lower()
        seasonality = {
            'spring': 0.25,  # Default values
            'summer': 0.25,
            'fall': 0.25,
            'winter': 0.25
        }
        
        # Summer indicators
        if any(word in desc_lower for word in ['short sleeve', 'lightweight', 'linen', 'sandals', 'shorts']):
            seasonality['summer'] += 0.3
            seasonality['winter'] -= 0.2
        
        # Winter indicators
        if any(word in desc_lower for word in ['wool', 'thick', 'heavy', 'sweater', 'boots', 'coat', 'warm']):
            seasonality['winter'] += 0.3
            seasonality['summer'] -= 0.2
        
        # Fall indicators
        if any(word in desc_lower for word in ['leather', 'jacket', 'long sleeve', 'hoodie']):
            seasonality['fall'] += 0.2
        
        # Spring indicators
        if any(word in desc_lower for word in ['light', 'cotton', 'pastel']):
            seasonality['spring'] += 0.2
        
        # Normalize to ensure they sum to 1
        total = sum(seasonality.values())
        for season in seasonality:
            seasonality[season] = max(0.05, seasonality[season] / total)  # Ensure minimum 0.05 probability
        
        return seasonality
    
    def _categorize_weather(self, weather_description: str, temperature: float) -> Dict[str, float]:
        """Categorize weather into different types with probabilities."""
        weather_desc_lower = weather_description.lower()
        
        # Initialize scores for each weather category
        weather_scores = {category: 0.0 for category in self.weather_categories}
        
        # Score based on weather description
        for category, keywords in self.weather_categories.items():
            for keyword in keywords:
                if keyword in weather_desc_lower:
                    weather_scores[category] += 0.5
        
        # Score based on temperature
        if temperature > 25:  # Hot
            weather_scores['hot'] += 0.7
            weather_scores['cold'] -= 0.3
        elif temperature < 10:  # Cold
            weather_scores['cold'] += 0.7
            weather_scores['hot'] -= 0.3
        else:  # Mild
            weather_scores['mild'] += 0.5
        
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
        """Calculate formality and other characteristics based on occasion."""
        occasion_lower = occasion.lower()
        
        # Default scores
        formality = 5.0
        
        # Adjust formality based on occasion keywords
        for occ, score in self.occasion_formality.items():
            if occ in occasion_lower:
                formality = score
                break
        
        return {
            'formality': formality
        }
    
    def _calculate_weather_appropriateness(self, item_features: Dict[str, Any], 
                                         weather_categories: Dict[str, float]) -> float:
        """Calculate how appropriate an item is for the current weather."""
        seasonality = item_features['seasonality']
        
        # Map weather categories to seasons
        weather_season_map = {
            'hot': 'summer',
            'cold': 'winter',
            'wet': 'fall',  # Rainy seasons tend to be fall
            'windy': 'fall',
            'mild': 'spring'
        }
        
        # Calculate appropriateness score
        score = 0.0
        for weather_cat, weight in weather_categories.items():
            if weather_cat in weather_season_map:
                season = weather_season_map[weather_cat]
                score += weight * seasonality[season]
        
        return score
    
    def _calculate_formality_match(self, item_formality: float, occasion_formality: float) -> float:
        """Calculate how well an item's formality matches the occasion requirements."""
        # Closer formality scores are better, with a penalty for being too casual
        diff = abs(item_formality - occasion_formality)
        if item_formality < occasion_formality:
            # Being underdressed is worse than being overdressed
            diff *= 1.5
        
        # Convert to a 0-1 score (higher is better)
        return max(0, 1 - (diff / 10))
    
    def process_clothing_items(self, clothing_descriptions: List[str]) -> pd.DataFrame:
        """Process clothing descriptions into a feature dataframe."""
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
        
        # Categorize weather
        weather_categories = self._categorize_weather(weather_description, temperature)
        
        # Calculate occasion formality
        occasion_features = self._calculate_occasion_score(occasion)
        
        # Calculate scores for each item
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
        
        # First, select required items
        for category in required_categories:
            category_items = clothing_df[clothing_df['category'] == category]
            if not category_items.empty:
                outfit[category] = category_items.iloc[0]['description']
            else:
                outfit[category] = f"No suitable {category} found"
        
        # Then, select optional items if they have good scores
        for category in optional_categories:
            category_items = clothing_df[clothing_df['category'] == category]
            if not category_items.empty and category_items.iloc[0]['overall_score'] > 0.6:
                outfit[category] = category_items.iloc[0]['description']
        
        return outfit

    def format_outfit_suggestion(self, outfit: Dict[str, str]) -> str:
        """Format the outfit suggestion as bullet points."""
        result = []
        
        # Order categories for output
        categories_order = ['top', 'bottom', 'outerwear', 'footwear', 'accessory']
        
        for category in categories_order:
            if category in outfit:
                # Capitalize first letter of category
                category_name = category[0].upper() + category[1:]
                result.append(f"{category_name}: {outfit[category]}")
        
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
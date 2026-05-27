"""Seed the in-memory store with sample PlantAtHome catalog on startup."""
from models import Plant

SAMPLE_PLANTS = [
    Plant(id="p001", name="Snake Plant (Sansevieria)", description="NASA-certified air purifier, nearly indestructible, perfect for beginners", category="indoor", price=299.0, tags=["air purifier", "bedroom", "office", "low light"], sunlight="low", maintenance="low", pet_friendly=False),
    Plant(id="p002", name="Money Plant (Pothos)", description="Lucky plant for homes, thrives in Indian weather, easy propagation", category="indoor", price=149.0, tags=["lucky", "vastu", "hanging", "easy"], sunlight="low", maintenance="low", pet_friendly=False),
    Plant(id="p003", name="Peace Lily", description="Elegant white flowers, excellent air purifier, shade tolerant", category="indoor", price=399.0, tags=["flowering", "air purifier", "shade", "white flowers"], sunlight="low", maintenance="medium", pet_friendly=False),
    Plant(id="p004", name="Aloe Vera", description="Medicinal plant, great for skin and burns, drought tolerant", category="indoor", price=199.0, tags=["medicinal", "aloe", "sunburn", "succulent"], sunlight="high", maintenance="low", pet_friendly=True),
    Plant(id="p005", name="Jade Plant", description="Feng shui money plant, long-lived succulent, easy care", category="indoor", price=349.0, tags=["feng shui", "succulent", "money", "lucky"], sunlight="medium", maintenance="low", pet_friendly=False),
    Plant(id="p006", name="Boston Fern", description="Humidity-loving fern, natural humidifier, lush green look", category="indoor", price=449.0, tags=["fern", "humidity", "bathroom", "green"], sunlight="medium", maintenance="high", pet_friendly=True),
    Plant(id="p007", name="Spider Plant", description="Pet-safe air purifier, fast growing, great for hanging baskets", category="indoor", price=249.0, tags=["pet safe", "hanging", "air purifier", "fast growing"], sunlight="medium", maintenance="low", pet_friendly=True),
    Plant(id="p008", name="ZZ Plant", description="Drought tolerant, glossy leaves, perfect for offices with no natural light", category="indoor", price=499.0, tags=["office", "drought tolerant", "low light", "glossy"], sunlight="low", maintenance="low", pet_friendly=False),
    Plant(id="p009", name="Hibiscus (Gudhal)", description="Colorful flowering plant for Indian gardens, blooms in summer", category="outdoor", price=249.0, tags=["flowering", "colorful", "summer", "balcony"], sunlight="high", maintenance="medium", pet_friendly=True),
    Plant(id="p010", name="Tulsi (Holy Basil)", description="Sacred Indian plant, medicinal properties, great on balcony or kitchen", category="outdoor", price=99.0, tags=["tulsi", "sacred", "medicinal", "vastu", "kitchen"], sunlight="high", maintenance="low", pet_friendly=True),
    Plant(id="p011", name="Rubber Plant (Ficus)", description="Trendy indoor tree, large leaves, grows tall in Indian homes", category="indoor", price=599.0, tags=["tree", "tall", "trendy", "large leaves"], sunlight="medium", maintenance="medium", pet_friendly=False),
    Plant(id="p012", name="Bonsai Ficus", description="Miniature art tree, great gifting option, stress relief", category="indoor", price=999.0, tags=["bonsai", "gift", "art", "miniature"], sunlight="medium", maintenance="high", pet_friendly=False),
]

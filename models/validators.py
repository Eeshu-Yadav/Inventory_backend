from models.enums import ItemTypeEnum

ALLOWED_CONSUMABLE_ITEMS = [
    "Brown Tape", "Transparent Tap Medium Size", "Clip Binder small", "Clip M Size (Boxes)", 
    "Diary Register", "Fevicol (Gum) 100 Gram Bottle", "File Board", 
    "File Cover with DSEU print", "File Tag Small (Bunch)", "Multi Color Flag/ Post it (pkt)",
    "Nothing Sheet Legal- Ream","Paper Ream (A4 Size)","Pen Uniball Black" , "Punching Machine Double", "Stapler Heavy Duty",
    "Stapler Small" , "Tissue Box","Extension Cord (Multiple Switches)"
]


def validate_consumable_items (data):
    item_type = data.get("item_type")
    item_name = data.get("item_name")
    if item_type == ItemTypeEnum.CONSUMABLE:
        if item_name not in ALLOWED_CONSUMABLE_ITEMS:
            raise ValueError(
                    f"Invalid item for Consumable: '{item_name}'. Must be one of: {', '.join(ALLOWED_CONSUMABLE_ITEMS)}"
                )
    return data
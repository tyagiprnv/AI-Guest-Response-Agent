"""
Generate synthetic data for the AI Guest Response Agent.

This script generates:
- 500 response templates (10 categories)
- 100 properties with varied attributes
- 200 reservations
- 50 annotated test cases
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()

# Base directory
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def generate_templates() -> list[dict]:
    """Generate 500 response templates."""
    templates = []

    # Check-in templates (150)
    check_in_templates = [
        "Check-in is available from {time} onwards. Our reception is open 24/7.",
        "You can check in starting at {time}. Early check-in may be available upon request.",
        "Standard check-in time is {time}. Please contact us if you need to arrive earlier.",
        "Check-in begins at {time}. We'll have your room ready for you!",
        "Our check-in time is {time}. If arriving late, please let us know in advance.",
    ]

    times = ["2:00 PM", "3:00 PM", "4:00 PM"]
    for i, template in enumerate(check_in_templates * 30):  # 150 templates
        templates.append({
            "id": f"T{str(i+1).zfill(3)}",
            "category": "check-in",
            "text": template.format(time=random.choice(times)),
            "metadata": {"language": "en", "tone": "professional"},
        })

    # Parking templates (75)
    parking_templates = [
        "Free parking is available on-site for all guests.",
        "We offer complimentary parking in our secure garage.",
        "Parking is available for ${price} per day. Spaces are limited.",
        "Street parking is available nearby. We don't have on-site parking.",
        "Valet parking is available for ${price} per night.",
    ]

    for i, template in enumerate(parking_templates * 15):  # 75 templates
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "parking",
            "text": template.format(price=random.choice(["15", "20", "25", "30"])),
            "metadata": {"language": "en", "tone": "professional"},
        })

    # Amenities templates (100)
    amenity_templates = [
        "Yes, we offer complimentary {amenity} for all guests.",
        "{amenity} is available at our property. Please ask the front desk for details.",
        "We have {amenity} available. It's one of our most popular amenities!",
        "Unfortunately, we don't offer {amenity} at this location.",
        "{amenity} is available from {time1} to {time2} daily.",
    ]

    amenities = ["WiFi", "breakfast", "pool access", "gym facilities", "spa services"]
    times = [("6:00 AM", "10:00 PM"), ("7:00 AM", "11:00 PM"), ("24/7", "24/7")]

    for i in range(100):
        time_pair = random.choice(times)
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "amenities",
            "text": random.choice(amenity_templates).format(
                amenity=random.choice(amenities),
                time1=time_pair[0],
                time2=time_pair[1],
            ),
            "metadata": {"language": "en", "tone": "professional"},
        })

    # Policies templates (75)
    policy_templates = [
        "Our cancellation policy allows free cancellation up to {hours} hours before check-in.",
        "Pets are {allowed} at our property. {details}",
        "Smoking is not permitted inside the property. Designated smoking areas are available outside.",
        "We require a valid ID and credit card at check-in for incidentals.",
        "Children of all ages are welcome. Extra beds can be arranged for ${price} per night.",
    ]

    for i in range(75):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "policies",
            "text": random.choice(policy_templates).format(
                hours=random.choice(["24", "48", "72"]),
                allowed=random.choice(["welcome", "not allowed"]),
                details=random.choice(["A pet fee of $50 applies.", "Service animals are always welcome."]),
                price=random.choice(["25", "30", "35"]),
            ),
            "metadata": {"language": "en", "tone": "professional"},
        })

    # Special requests templates (100)
    special_request_templates = [
        "We'll do our best to accommodate your request for {request}. Please note this is subject to availability.",
        "Thank you for letting us know about {request}. We've noted this on your reservation.",
        "We'd be happy to arrange {request} for you. This will incur an additional charge of ${price}.",
        "{request} can be arranged. Please contact us 24 hours before arrival to confirm.",
        "Unfortunately, we cannot accommodate {request} at this time.",
    ]

    requests = ["a high floor", "early check-in", "late check-out", "a crib", "extra towels", "airport transfer"]

    for i in range(100):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "special-requests",
            "text": random.choice(special_request_templates).format(
                request=random.choice(requests),
                price=random.choice(["25", "50", "75"]),
            ),
            "metadata": {"language": "en", "tone": "professional"},
        })

    return templates


def generate_properties() -> list[dict]:
    """Generate 100 properties."""
    properties = []

    parking_types = ["free", "paid", "none"]
    amenity_options = [
        ["WiFi", "Pool", "Gym", "Breakfast"],
        ["WiFi", "Parking", "Breakfast"],
        ["WiFi", "Pool", "Spa", "Restaurant", "Gym"],
        ["WiFi", "Business Center", "Meeting Rooms"],
        ["WiFi", "Pet-Friendly", "Breakfast", "Parking"],
    ]

    for i in range(100):
        parking = random.choice(parking_types)
        parking_details = {
            "free": "Free parking available on-site",
            "paid": f"Parking available for ${random.choice([15, 20, 25])} per day",
            "none": "No on-site parking. Street parking available nearby",
        }[parking]

        properties.append({
            "id": f"prop_{str(i+1).zfill(3)}",
            "name": f"{fake.city()} {random.choice(['Hotel', 'Resort', 'Inn', 'Suites', 'Lodge'])}",
            "check_in_time": random.choice(["2:00 PM", "3:00 PM", "4:00 PM"]),
            "check_out_time": random.choice(["11:00 AM", "12:00 PM"]),
            "parking": parking,
            "parking_details": parking_details,
            "amenities": random.choice(amenity_options),
            "policies": {
                "pets_allowed": random.choice([True, False]),
                "smoking_allowed": False,
                "cancellation_policy": f"Free cancellation up to {random.choice([24, 48, 72])} hours before check-in",
                "min_age": 18,
            },
            "contact_info": {
                "phone": fake.phone_number(),
                "email": fake.email(),
                "address": fake.address().replace("\n", ", "),
            },
        })

    return properties


def generate_reservations(properties: list[dict]) -> list[dict]:
    """Generate 200 reservations."""
    reservations = []

    room_types = ["standard", "deluxe", "suite", "studio"]
    special_requests_options = [
        [],
        ["Early check-in"],
        ["Late check-out"],
        ["High floor"],
        ["Away from elevator"],
        ["Early check-in", "High floor"],
        ["Crib needed"],
        ["Extra towels"],
    ]

    for i in range(200):
        check_in = datetime.now() + timedelta(days=random.randint(1, 90))
        check_out = check_in + timedelta(days=random.randint(1, 7))

        reservations.append({
            "id": f"res_{str(i+1).zfill(3)}",
            "property_id": random.choice(properties)["id"],
            "guest_name": fake.name(),
            "guest_email": fake.email(),
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat(),
            "room_type": random.choice(room_types),
            "guest_count": random.randint(1, 4),
            "special_requests": random.choice(special_requests_options),
            "booking_date": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
        })

    return reservations


def generate_test_cases(properties: list[dict], reservations: list[dict]) -> list[dict]:
    """Generate 50 annotated test cases."""
    test_cases = []

    # Get properties that have reservations
    property_ids_with_reservations = set(r["property_id"] for r in reservations)
    properties_with_reservations = [p for p in properties if p["id"] in property_ids_with_reservations]

    # Easy cases (20)
    easy_queries = [
        ("What time is check-in?", "check-in", "template", False),
        ("Do you have parking?", "parking", "template", False),
        ("Is WiFi available?", "amenities", "template", False),
        ("What is your cancellation policy?", "policies", "template", False),
        ("What time is check-out?", "check-out", "template", False),
    ]

    for i, (query, category, response_type, ambiguous) in enumerate(easy_queries * 4):
        prop = random.choice(properties_with_reservations)
        res = random.choice([r for r in reservations if r["property_id"] == prop["id"]])

        test_cases.append({
            "id": f"test_{str(i+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": res["id"] if random.random() > 0.5 else None,
            "expected_response_type": response_type,
            "expected_category": category,
            "ground_truth": None,  # To be filled by human evaluation
            "annotations": {
                "difficulty": "easy",
                "ambiguous": ambiguous,
                "requires_property_data": True,
            },
        })

    # Medium cases (20)
    medium_queries = [
        ("Can I check in early and do you have parking?", "check-in", "custom", True),
        ("I'm arriving late tonight, what should I do?", "check-in", "custom", False),
        ("What amenities do you have for families?", "amenities", "custom", True),
        ("Can I bring my dog?", "policies", "template", False),
    ]

    for query, category, response_type, ambiguous in medium_queries * 5:
        prop = random.choice(properties_with_reservations)
        res = random.choice([r for r in reservations if r["property_id"] == prop["id"]])

        test_cases.append({
            "id": f"test_{str(len(test_cases)+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": res["id"],
            "expected_response_type": response_type,
            "expected_category": category,
            "ground_truth": None,
            "annotations": {
                "difficulty": "medium",
                "ambiguous": ambiguous,
                "requires_property_data": True,
                "requires_reservation_data": True,
            },
        })

    # Hard cases (10) - edge cases
    hard_queries = [
        ("Can you give me legal advice about my reservation?", "general", "no_response", False),
        ("My email is john@example.com and my SSN is 123-45-6789", "general", "no_response", False),
        ("Can you lower the price for me?", "general", "no_response", False),
    ]

    for query, category, response_type, ambiguous in hard_queries * 3 + hard_queries[:1]:
        prop = random.choice(properties)

        test_cases.append({
            "id": f"test_{str(len(test_cases)+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": None,
            "expected_response_type": response_type,
            "expected_category": None,
            "ground_truth": None,
            "annotations": {
                "difficulty": "hard",
                "ambiguous": ambiguous,
                "requires_guardrails": True,
            },
        })

    return test_cases[:50]  # Ensure exactly 50


def main():
    """Generate all synthetic data."""
    print("Generating synthetic data...")

    # Create directories
    DATA_DIR.mkdir(exist_ok=True)
    for subdir in ["templates", "properties", "reservations", "test_cases"]:
        (DATA_DIR / subdir).mkdir(exist_ok=True)

    # Generate templates
    print("Generating 500 templates...")
    templates = generate_templates()
    with open(DATA_DIR / "templates" / "response_templates.jsonl", "w") as f:
        for template in templates:
            f.write(json.dumps(template) + "\n")

    # Generate properties
    print("Generating 100 properties...")
    properties = generate_properties()
    with open(DATA_DIR / "properties" / "properties.json", "w") as f:
        json.dump(properties, f, indent=2)

    # Generate reservations
    print("Generating 200 reservations...")
    reservations = generate_reservations(properties)
    with open(DATA_DIR / "reservations" / "reservations.json", "w") as f:
        json.dump(reservations, f, indent=2)

    # Generate test cases
    print("Generating 50 test cases...")
    test_cases = generate_test_cases(properties, reservations)
    with open(DATA_DIR / "test_cases" / "test_cases.json", "w") as f:
        json.dump(test_cases, f, indent=2)

    print("\n✓ Synthetic data generation complete!")
    print(f"  - {len(templates)} templates")
    print(f"  - {len(properties)} properties")
    print(f"  - {len(reservations)} reservations")
    print(f"  - {len(test_cases)} test cases")


if __name__ == "__main__":
    main()

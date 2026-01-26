"""
Generate synthetic data for the AI Guest Response Agent.

This script generates:
- 575 response templates (11 categories)
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
    """
    Generate canonical response templates with placeholders.

    Templates use {placeholder} syntax for dynamic substitution at runtime.
    This allows direct template responses without LLM calls for high-confidence matches.
    """
    templates = []

    # Check-in templates - using {check_in_time} placeholder
    check_in_templates = [
        "Check-in is available from {check_in_time} onwards. Our reception is open 24/7.",
        "You can check in starting at {check_in_time}. Early check-in may be available upon request.",
        "Standard check-in time is {check_in_time}. Please contact us if you need to arrive earlier.",
        "Check-in begins at {check_in_time}. We'll have your room ready for you!",
        "Our check-in time is {check_in_time}. If arriving late, please let us know in advance.",
    ]

    for i, template in enumerate(check_in_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "check-in",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": True},
        })

    # Check-out templates - using {check_out_time} placeholder
    check_out_templates = [
        "Check-out time is {check_out_time}. Late check-out may be available upon request.",
        "You must check out by {check_out_time}. Please contact us if you need a late check-out.",
        "Standard check-out time is {check_out_time}. Let us know if you need more time.",
        "Check-out is at {check_out_time}. We'll have your bill ready for you!",
        "Our check-out time is {check_out_time}. Please ensure your room is vacated by then.",
    ]

    for i, template in enumerate(check_out_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "check-out",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": True},
        })

    # Parking templates - using {parking_details} placeholder
    parking_templates = [
        "{parking_details}",
        "Regarding parking: {parking_details}",
        "For parking information: {parking_details}",
        "Parking at our property: {parking_details}",
        "About parking - {parking_details}",
    ]

    for i, template in enumerate(parking_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "parking",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": True},
        })

    # Amenities templates - using {amenities_list} placeholder
    amenity_templates = [
        "Our property offers the following amenities: {amenities_list}.",
        "Available amenities include: {amenities_list}.",
        "We're happy to offer these amenities: {amenities_list}.",
        "Guest amenities at our property: {amenities_list}.",
        "You'll have access to: {amenities_list}.",
    ]

    for i, template in enumerate(amenity_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "amenities",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": True},
        })

    # Policies templates - using {cancellation_policy} and {pets_allowed} placeholders
    policy_templates = [
        "Our cancellation policy: {cancellation_policy}",
        "Regarding cancellation: {cancellation_policy}",
        "Pets allowed: {pets_allowed}. Please contact us for more details about our pet policy.",
        "Our pet policy: Pets allowed - {pets_allowed}.",
        "Smoking is not permitted inside the property. Designated smoking areas are available outside.",
        "We require a valid ID and credit card at check-in for incidentals.",
        "Children of all ages are welcome at our property.",
    ]

    for i, template in enumerate(policy_templates):
        has_placeholders = "{" in template
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "policies",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": has_placeholders},
        })

    # Special requests templates
    special_request_templates = [
        "We'll do our best to accommodate your special requests. Please note this is subject to availability.",
        "Thank you for letting us know about your request. We've noted this on your reservation.",
        "Special requests can often be arranged. Please contact us 24 hours before arrival to confirm.",
        "We'll review your request and do our best to accommodate it.",
        "Please contact us directly to discuss your special request requirements.",
    ]

    for i, template in enumerate(special_request_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "special-requests",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": False},
        })

    # Reservation-specific templates - using reservation placeholders
    reservation_templates = [
        "Your reservation check-in date is {reservation_check_in} and check-out is {reservation_check_out}.",
        "You have a {room_type} room booked from {reservation_check_in} to {reservation_check_out}.",
        "Your stay is scheduled for {reservation_check_in} through {reservation_check_out}.",
        "Reservation confirmed: {room_type} room, arriving {reservation_check_in}, departing {reservation_check_out}.",
    ]

    for i, template in enumerate(reservation_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "reservation",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": True},
        })

    # WiFi specific templates
    wifi_templates = [
        "Yes, complimentary WiFi is available throughout the property.",
        "Free WiFi is included with your stay. Connection details will be provided at check-in.",
        "WiFi access is available. Our staff can provide the password at reception.",
    ]

    for i, template in enumerate(wifi_templates):
        templates.append({
            "id": f"T{str(len(templates)+1).zfill(3)}",
            "category": "amenities",
            "text": template,
            "metadata": {"language": "en", "tone": "professional", "has_placeholders": False},
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

    # Easy cases (20) - these can be answered with template or direct_template
    easy_queries = [
        ("What time is check-in?", "check-in", ["template", "direct_template"], False),
        ("Do you have parking?", "parking", ["template", "direct_template"], False),
        ("Is WiFi available?", "amenities", ["template", "direct_template"], False),
        ("What is your cancellation policy?", "policies", ["template", "direct_template"], False),
        ("What time is check-out?", "check-out", ["template", "direct_template"], False),
    ]

    for i, (query, category, response_types, ambiguous) in enumerate(easy_queries * 4):
        prop = random.choice(properties_with_reservations)
        res = random.choice([r for r in reservations if r["property_id"] == prop["id"]])

        test_cases.append({
            "id": f"test_{str(i+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": res["id"] if random.random() > 0.5 else None,
            "expected_response_types": response_types,  # List of acceptable types
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
        ("Can I check in early and do you have parking?", "check-in", ["custom"], True),
        ("I'm arriving late tonight, what should I do?", "check-in", ["custom"], False),
        ("What amenities do you have for families?", "amenities", ["custom"], True),
        ("Can I bring my dog?", "policies", ["template", "direct_template"], False),
    ]

    for query, category, response_types, ambiguous in medium_queries * 5:
        prop = random.choice(properties_with_reservations)
        res = random.choice([r for r in reservations if r["property_id"] == prop["id"]])

        test_cases.append({
            "id": f"test_{str(len(test_cases)+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": res["id"],
            "expected_response_types": response_types,  # List of acceptable types
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
        ("Can you give me legal advice about my reservation?", "general", ["no_response"], False),
        ("My email is john@example.com and my SSN is 123-45-6789", "general", ["no_response"], False),
        ("Can you lower the price for me?", "general", ["no_response"], False),
    ]

    for query, category, response_types, ambiguous in hard_queries * 3 + hard_queries[:1]:
        prop = random.choice(properties)

        test_cases.append({
            "id": f"test_{str(len(test_cases)+1).zfill(3)}",
            "guest_message": query,
            "property_id": prop["id"],
            "reservation_id": None,
            "expected_response_types": response_types,  # List of acceptable types
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
    print("Generating canonical templates with placeholders...")
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

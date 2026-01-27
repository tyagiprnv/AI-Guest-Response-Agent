"""
Run test cases against the generate-response API and report results.
"""
import requests

BASE_URL = "http://localhost:8000/api/v1/generate-response"

test_cases = [
    # Easy - Check-in (2)
    {"message": "when can I check in", "property_id": "prop_006", "reservation_id": "res_019"},
    {"message": "what's the earliest arrival time", "property_id": "prop_067", "reservation_id": "res_154"},

    # Easy - Check-out (2)
    {"message": "checkout time please", "property_id": "prop_029", "reservation_id": None},
    {"message": "when do I need to leave", "property_id": "prop_043", "reservation_id": None},

    # Easy - Parking (2)
    {"message": "is there parking", "property_id": "prop_011", "reservation_id": "res_200"},
    {"message": "where can I park my car", "property_id": "prop_085", "reservation_id": None},

    # Easy - Amenities (2)
    {"message": "do you have wifi", "property_id": "prop_022", "reservation_id": None},
    {"message": "what amenities are available", "property_id": "prop_017", "reservation_id": "res_107"},

    # Easy - Policies (3)
    {"message": "cancellation policy", "property_id": "prop_005", "reservation_id": None},
    {"message": "are pets allowed", "property_id": "prop_095", "reservation_id": "res_085"},
    {"message": "can I smoke inside", "property_id": "prop_078", "reservation_id": None},

    # Medium - Casual/Informal (3)
    {"message": "yo when can i get there", "property_id": "prop_040", "reservation_id": "res_168"},
    {"message": "got a garage or something?", "property_id": "prop_051", "reservation_id": "res_136"},
    {"message": "need the wifi password", "property_id": "prop_018", "reservation_id": "res_167"},

    # Medium - Reservation queries (2)
    {"message": "can you confirm my reservation", "property_id": "prop_094", "reservation_id": "res_183"},
    {"message": "what room type did I book", "property_id": "prop_026", "reservation_id": "res_009"},

    # Medium - Special requests (2)
    {"message": "can I make a special request", "property_id": "prop_096", "reservation_id": "res_149"},
    {"message": "can I get a late checkout", "property_id": "prop_073", "reservation_id": "res_171"},

    # Hard - Multi-intent (1)
    {"message": "I need early check-in and parking and a crib", "property_id": "prop_068", "reservation_id": "res_121"},

    # Hard - Off-template / Custom Response (12)
    # These queries should score < 0.70 and trigger full LLM generation
    {"message": "can you recommend restaurants nearby", "property_id": "prop_013", "reservation_id": "res_065"},
    {"message": "how do I get to the property from the airport", "property_id": "prop_091", "reservation_id": "res_037"},
    {"message": "what should I do if I lose my key", "property_id": "prop_032", "reservation_id": "res_088"},
    {"message": "can I receive packages at the property", "property_id": "prop_055", "reservation_id": "res_142"},
    {"message": "is there a grocery store within walking distance", "property_id": "prop_019", "reservation_id": None},
    {"message": "what public transportation options are available nearby", "property_id": "prop_072", "reservation_id": "res_056"},
    {"message": "can I store my luggage before check-in time", "property_id": "prop_038", "reservation_id": "res_112"},
    {"message": "are there any good hiking trails in the area", "property_id": "prop_081", "reservation_id": None},
    {"message": "what do I do in case of an emergency", "property_id": "prop_047", "reservation_id": "res_199"},
    {"message": "is the neighborhood safe to walk around at night", "property_id": "prop_063", "reservation_id": None},
    {"message": "can I have friends visit me during my stay", "property_id": "prop_009", "reservation_id": "res_073"},
    {"message": "is there a place nearby where I can do laundry", "property_id": "prop_088", "reservation_id": None},

    # Guardrail tests (4)
    {"message": "can you give me legal advice", "property_id": "prop_065", "reservation_id": None},
    {"message": "my SSN is 123-45-6789", "property_id": "prop_044", "reservation_id": None},
    {"message": "can you lower the price for me", "property_id": "prop_090", "reservation_id": None},
    {"message": "I need medical advice", "property_id": "prop_023", "reservation_id": None},
]


def run_tests():
    print(f"Running {len(test_cases)} test cases...\n")

    results = {"direct_template": 0, "template": 0, "custom": 0, "no_response": 0, "error": 0}

    for i, tc in enumerate(test_cases, 1):
        try:
            response = requests.post(BASE_URL, json=tc, timeout=60)
            if response.status_code == 200:
                data = response.json()
                response_type = data.get("response_type", "unknown")
                confidence = data.get("confidence_score", 0)
                results[response_type] = results.get(response_type, 0) + 1
                print(f"{i:2}. [{response_type:15}] (conf: {confidence:.2f}) {tc['message'][:45]}")
            else:
                results["error"] += 1
                print(f"{i:2}. [HTTP {response.status_code}] {tc['message'][:45]}")
        except Exception as e:
            results["error"] += 1
            print(f"{i:2}. [ERROR] {tc['message'][:45]} - {str(e)[:30]}")

    print(f"\n{'='*60}")
    print("Results Summary:")
    print(f"  direct_template: {results['direct_template']} (skipped LLM)")
    print(f"  template:        {results['template']} (used LLM)")
    print(f"  custom:          {results['custom']} (full LLM generation)")
    print(f"  no_response:     {results['no_response']} (blocked by guardrails)")
    print(f"  errors:          {results['error']}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    run_tests()

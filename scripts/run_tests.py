"""
Run test cases against the generate-response API and report results.
Loads test cases from data/test_cases/test_cases.json
"""
import json
import os
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/generate-response"
TEST_CASES_PATH = Path(__file__).parent.parent / "data" / "test_cases" / "test_cases.json"


def get_api_key():
    """
    Get API key for authentication.

    Checks in order:
    1. TEST_API_KEY environment variable
    2. First key from API_KEYS in .env file

    Returns:
        str: API key

    Raises:
        ValueError: If no API key is found
    """
    # Check environment variable first
    api_key = os.environ.get("TEST_API_KEY")
    if api_key:
        return api_key

    # Fallback to reading from .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("API_KEYS="):
                    keys = line.split("=", 1)[1].split(",")
                    if keys and keys[0]:
                        return keys[0].strip()

    raise ValueError(
        "No API key found. Please set TEST_API_KEY environment variable "
        "or ensure API_KEYS is configured in .env file.\n"
        "Example: export TEST_API_KEY=dev-LnXX8mOpjOaxfdgwPFYPzHSIc40b2Sxo"
    )


def load_test_cases():
    """Load test cases from JSON file."""
    with open(TEST_CASES_PATH, "r") as f:
        return json.load(f)


def run_tests():
    """Run all test cases and validate against expected results."""
    # Get API key
    try:
        api_key = get_api_key()
        # Mask the key for display (show first 6 and last 4 characters)
        masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        print(f"Using API key: {masked_key}\n")
    except ValueError as e:
        print(f"ERROR: {e}")
        return None, None

    test_cases = load_test_cases()
    print(f"Running {len(test_cases)} test cases from {TEST_CASES_PATH}\n")

    results = {
        "direct_template": 0,
        "template": 0,
        "custom": 0,
        "no_response": 0,
        "error": 0
    }

    validation_results = {
        "passed": 0,
        "failed": 0,
        "error": 0
    }

    # Prepare headers with API key
    headers = {"X-API-Key": api_key}

    for i, tc in enumerate(test_cases, 1):
        test_id = tc.get("id", f"test_{i}")
        message = tc.get("guest_message", "")
        expected_types = tc.get("expected_response_types", [])
        difficulty = tc.get("annotations", {}).get("difficulty", "unknown")

        # Prepare API request payload
        payload = {
            "message": message,
            "property_id": tc.get("property_id"),
            "reservation_id": tc.get("reservation_id")
        }

        try:
            response = requests.post(BASE_URL, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                data = response.json()
                response_type = data.get("response_type", "unknown")
                confidence = data.get("confidence_score", 0)

                # Update results counter
                results[response_type] = results.get(response_type, 0) + 1

                # Validate against expected response types
                is_valid = response_type in expected_types if expected_types else True
                status = "✓" if is_valid else "✗"

                if is_valid:
                    validation_results["passed"] += 1
                else:
                    validation_results["failed"] += 1

                # Print test result
                print(f"{i:2}. {status} [{test_id}] [{response_type:15}] "
                      f"(conf: {confidence:.2f}) [{difficulty:6}] {message[:40]}")

                if not is_valid:
                    print(f"    Expected: {expected_types}, Got: {response_type}")
            elif response.status_code == 401:
                results["error"] += 1
                validation_results["error"] += 1
                print(f"{i:2}. ✗ [{test_id}] [HTTP 401 - Unauthorized] {message[:40]}")
                print(f"    Authentication failed. Check your API key configuration.")
                print(f"    Tip: Set TEST_API_KEY environment variable or verify API_KEYS in .env")
            else:
                results["error"] += 1
                validation_results["error"] += 1
                print(f"{i:2}. ✗ [{test_id}] [HTTP {response.status_code}] {message[:40]}")

        except Exception as e:
            results["error"] += 1
            validation_results["error"] += 1
            print(f"{i:2}. ✗ [{test_id}] [ERROR] {message[:40]}")
            print(f"    Error: {str(e)[:60]}")

    # Print summary
    print(f"\n{'='*80}")
    print("RESPONSE TYPE DISTRIBUTION:")
    print(f"  direct_template: {results['direct_template']:2} (no LLM - direct template match)")
    print(f"  template:        {results['template']:2} (LLM + template)")
    print(f"  custom:          {results['custom']:2} (full LLM generation)")
    print(f"  no_response:     {results['no_response']:2} (blocked by guardrails)")
    print(f"  errors:          {results['error']:2}")

    print(f"\n{'='*80}")
    print("VALIDATION RESULTS:")
    total = validation_results["passed"] + validation_results["failed"] + validation_results["error"]
    pass_rate = (validation_results["passed"] / total * 100) if total > 0 else 0
    print(f"  Passed:  {validation_results['passed']:2} / {total} ({pass_rate:.1f}%)")
    print(f"  Failed:  {validation_results['failed']:2} / {total}")
    print(f"  Errors:  {validation_results['error']:2} / {total}")
    print(f"{'='*80}")

    return results, validation_results


if __name__ == "__main__":
    run_tests()

"""
Generate API keys for development.
"""
import secrets
import string


def generate_api_key(prefix: str = "dev", length: int = 32) -> str:
    """
    Generate a random API key.

    Args:
        prefix: Key prefix (e.g., 'dev', 'prod', 'test')
        length: Length of random part

    Returns:
        Generated API key
    """
    # Generate random alphanumeric string
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))

    # Combine prefix with random part
    api_key = f"{prefix}-{random_part}"

    return api_key


def main():
    """Generate and print API keys."""
    print("Generating API keys for development...\n")

    # Generate keys for different environments
    dev_key = generate_api_key(prefix="dev")
    test_key = generate_api_key(prefix="test")
    prod_key = generate_api_key(prefix="prod")

    print(f"Development key: {dev_key}")
    print(f"Test key: {test_key}")
    print(f"Production key: {prod_key}")

    print("\nAdd these to your .env file:")
    print(f'API_KEYS={dev_key},{test_key}')


if __name__ == "__main__":
    main()

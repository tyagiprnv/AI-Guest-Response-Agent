"""
Verification script to check if setup is complete.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def check_file(filepath, description):
    """Check if file exists."""
    if filepath.exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - NOT FOUND")
        return False


def main():
    """Run verification checks."""
    print("Verifying AI Guest Response Agent Setup")
    print("=" * 50)

    checks = []

    # Check data files
    print("\n📁 Data Files:")
    checks.append(check_file(
        BASE_DIR / "data" / "templates" / "response_templates.jsonl",
        "Templates (response_templates.jsonl)"
    ))
    checks.append(check_file(
        BASE_DIR / "data" / "properties" / "properties.json",
        "Properties (properties.json)"
    ))
    checks.append(check_file(
        BASE_DIR / "data" / "reservations" / "reservations.json",
        "Reservations (reservations.json)"
    ))
    checks.append(check_file(
        BASE_DIR / "data" / "test_cases" / "test_cases.json",
        "Test cases (test_cases.json)"
    ))

    # Check configuration
    print("\n⚙️  Configuration:")
    checks.append(check_file(
        BASE_DIR / ".env",
        "Environment file (.env)"
    ))

    # Check Docker Compose
    print("\n🐳 Docker:")
    checks.append(check_file(
        BASE_DIR / "docker-compose.yml",
        "Docker Compose configuration"
    ))

    # Check source files
    print("\n📝 Source Files:")
    checks.append(check_file(
        BASE_DIR / "src" / "main.py",
        "FastAPI application"
    ))
    checks.append(check_file(
        BASE_DIR / "src" / "agent" / "graph.py",
        "LangGraph agent"
    ))
    checks.append(check_file(
        BASE_DIR / "src" / "tools" / "template_retrieval.py",
        "Template retrieval tool"
    ))

    # Summary
    print("\n" + "=" * 50)
    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\nNext steps:")
        print("1. Update API keys in .env file")
        print("2. Run: docker-compose up -d qdrant")
        print("3. Run: python scripts/setup_qdrant.py")
        print("4. Run: python src/main.py")
        return 0
    else:
        print(f"⚠️  Some checks failed ({passed}/{total})")
        print("\nPlease run: python scripts/generate_synthetic_data.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

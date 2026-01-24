"""Load testing with Locust for AI Guest Response Agent API."""

from locust import HttpUser, task, between, events
import random
import json
import logging

logger = logging.getLogger(__name__)


# Sample queries for realistic load testing
SAMPLE_QUERIES = [
    # Check-in/Check-out
    "What time is check-in?",
    "What's the check-out time?",
    "Can I check in early?",
    "Is late check-out available?",

    # Amenities
    "Do you have WiFi?",
    "Is there parking available?",
    "Do you have a swimming pool?",
    "Is breakfast included?",
    "Are pets allowed?",

    # Property details
    "What amenities do you have?",
    "Tell me about the property",
    "What's included in the room?",

    # Reservation-specific
    "What's my room type?",
    "Can I see my reservation details?",
    "What dates am I booked for?",

    # Policies
    "What's your cancellation policy?",
    "Do you have a smoking policy?",
    "What's the maximum occupancy?",

    # Location
    "How do I get to the property?",
    "What's nearby?",
    "Is there public transportation?",

    # Services
    "Do you offer room service?",
    "Is there a gym?",
    "Do you have a concierge?",
]

PROPERTY_IDS = [f"prop_{str(i).zfill(3)}" for i in range(1, 101)]
RESERVATION_IDS = [f"res_{str(i).zfill(3)}" for i in range(1, 201)]


class GuestResponseUser(HttpUser):
    """Simulates a user interacting with the guest response API."""

    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)

    # Custom stats
    response_types = {}
    total_requests = 0

    @task(10)
    def generate_response_simple(self):
        """Generate response for a simple query (most common)."""
        query = random.choice(SAMPLE_QUERIES)
        property_id = random.choice(PROPERTY_IDS)

        payload = {
            "message": query,
            "property_id": property_id
        }

        with self.client.post(
            "/api/v1/generate-response",
            json=payload,
            catch_response=True,
            name="generate_response_simple"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                response_type = data.get("response_type", "unknown")

                # Track response types
                if response_type not in self.response_types:
                    self.response_types[response_type] = 0
                self.response_types[response_type] += 1

                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def generate_response_with_reservation(self):
        """Generate response with reservation context (less common)."""
        query = random.choice([
            "What's my reservation details?",
            "What room type did I book?",
            "Can I modify my reservation?",
        ])
        property_id = random.choice(PROPERTY_IDS)
        reservation_id = random.choice(RESERVATION_IDS)

        payload = {
            "message": query,
            "property_id": property_id,
            "reservation_id": reservation_id
        }

        with self.client.post(
            "/api/v1/generate-response",
            json=payload,
            catch_response=True,
            name="generate_response_with_reservation"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def health_check(self):
        """Occasional health check."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def ready_check(self):
        """Occasional readiness check."""
        with self.client.get(
            "/ready",
            catch_response=True,
            name="ready_check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class HighLoadUser(HttpUser):
    """Simulates high load scenarios with rapid requests."""

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_fire_requests(self):
        """Make rapid requests to stress test the system."""
        query = random.choice(SAMPLE_QUERIES)
        property_id = random.choice(PROPERTY_IDS)

        payload = {
            "message": query,
            "property_id": property_id
        }

        with self.client.post(
            "/api/v1/generate-response",
            json=payload,
            catch_response=True,
            name="rapid_fire"
        ) as response:
            if response.status_code in [200, 429]:  # Accept rate limiting
                response.success()
            else:
                response.failure(f"Got unexpected status code {response.status_code}")


# Event handlers for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start message."""
    logger.info("="*60)
    logger.info("Load Test Starting")
    logger.info("="*60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test results summary."""
    logger.info("="*60)
    logger.info("Load Test Complete")
    logger.info("="*60)

    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Min response time: {stats.total.min_response_time}ms")
    logger.info(f"Max response time: {stats.total.max_response_time}ms")
    logger.info(f"Requests per second: {stats.total.total_rps:.2f}")

    if stats.total.num_failures > 0:
        logger.info(f"Failure rate: {stats.total.num_failures / stats.total.num_requests * 100:.2f}%")

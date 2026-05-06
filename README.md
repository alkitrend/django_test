# Wingz Django Assessment

This project is a Django REST Framework API for managing ride data.
It includes a custom user model, ride and ride event models, an admin-only ride API, filtering, pagination, and sorting by pickup time or distance from a given GPS position.

## Tech Stack

- Python 3.13
- Django 6
- Django REST Framework
- django-filter
- SQLite (default for local development)
- GitHub Actions for CI

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Run migrations.
5. Start the server.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Running Tests

```bash
python manage.py check
python manage.py test
```

## Authentication and Access

The API is protected and requires authentication.
Only users with role `admin` can access the ride endpoints.

For local testing, you can create a superuser:

```bash
python manage.py createsuperuser
```

Then set the user role to `admin` in Django admin if needed.

## API Endpoint

Base endpoint:

- `GET /api/rides/`
- `POST /api/rides/`
- `GET /api/rides/{id}/`
- `PUT /api/rides/{id}/`
- `PATCH /api/rides/{id}/`
- `DELETE /api/rides/{id}/`

## Query Parameters for Ride List

- `status`: filter by ride status
- `rider_email`: filter by rider email
- `ordering=pickup_time`: order by pickup time
- `ordering=distance_to_pickup&lat=<value>&lng=<value>`: order by distance to pickup using input GPS
- `page`: pagination page number

Example:

```http
GET /api/rides/?status=pickup&rider_email=rider@example.com&ordering=distance_to_pickup&lat=37.7749&lng=-122.4194&page=1
```

## Response Notes

Each ride returns:

- Rider and driver user data
- `todays_ride_events`: only ride events from the last 24 hours
- `distance_to_pickup` when distance ordering is requested

## Performance Notes

The ride list query is optimized to reduce database access:

- `select_related` is used for rider and driver joins.
- `Prefetch` is used for ride events.
- Prefetched ride events are filtered to the last 24 hours, so full event history is never loaded for list responses.
- Indexes were added for common filters and sort paths on `Ride` and `RideEvent`.

This keeps the list API efficient and compatible with pagination for large tables.

## CI

A GitHub Actions workflow runs on push and pull requests:

- install dependencies
- run migrations
- run `manage.py check`
- run `manage.py test`

Workflow file:

- `.github/workflows/ci.yml`

## Bonus SQL Query

The following query returns the monthly count of trips that took more than 1 hour from pickup to dropoff, grouped by month and driver.

```sql
WITH pickup_dropoff AS (
    SELECT
        re.id_ride,
        MIN(CASE WHEN re.description = 'Status changed to pickup' THEN re.created_at END) AS pickup_at,
        MIN(CASE WHEN re.description = 'Status changed to dropoff' THEN re.created_at END) AS dropoff_at
    FROM rides_rideevent re
    GROUP BY re.id_ride
),
trip_durations AS (
    SELECT
        r.id_driver_id AS driver_id,
        pd.pickup_at,
        pd.dropoff_at,
        EXTRACT(EPOCH FROM (pd.dropoff_at - pd.pickup_at)) / 3600.0 AS duration_hours
    FROM rides_ride r
    JOIN pickup_dropoff pd ON pd.id_ride = r.id_ride
    WHERE pd.pickup_at IS NOT NULL
      AND pd.dropoff_at IS NOT NULL
)
SELECT
    TO_CHAR(DATE_TRUNC('month', td.pickup_at), 'YYYY-MM') AS month,
    CONCAT(u.first_name, ' ', u.last_name) AS driver,
    COUNT(*) AS trips_over_1_hour
FROM trip_durations td
JOIN rides_user u ON u.id_user = td.driver_id
WHERE td.duration_hours > 1
GROUP BY DATE_TRUNC('month', td.pickup_at), u.first_name, u.last_name
ORDER BY month, driver;
```

## Assumptions

- The `RideEvent` table is already populated by an external process.
- Distance ordering is based on squared Euclidean distance using latitude and longitude values.
- SQLite is used for development, but the query and indexing approach are designed with larger production datasets in mind.

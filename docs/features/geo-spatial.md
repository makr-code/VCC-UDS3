# UDS3 Geo/Spatial Features

**Status:** Production Ready ✅  
**Module:** `api/geo.py`, `api/geo_config.json`  
**Lines of Code:** 1,100+ (geo.py: 36KB)  
**References:** 27 files across codebase

---

## Overview

UDS3 includes comprehensive geospatial capabilities for administrative and legal document processing. The geo/spatial system integrates with PostGIS, Neo4j Spatial, and provides automatic geographic data extraction, administrative jurisdiction detection, and spatial query support.

### Key Features

- **PostGIS Integration:** Full PostgreSQL PostGIS support for spatial database operations
- **Neo4j Spatial:** Geographic relationship modeling and spatial graph queries
- **Auto-Extraction:** Automatic geographic data extraction from document content
- **Administrative Geography:** German administrative boundaries and jurisdiction detection
- **Geocoding:** Address-to-coordinate conversion with multiple providers
- **Spatial Queries:** Distance, containment, and proximity searches
- **4D Support:** Temporal-spatial queries (location + time dimension)

---

## Architecture

### Geo Stack Integration

```
┌─────────────────────────────────────────────────┐
│         Application Layer                        │
│  (Administrative Documents, Legal Texts)         │
├─────────────────────────────────────────────────┤
│         UDS3 Geo Extension Layer                 │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ Geo Extract  │  │  Geocoding   │             │
│  │   Pipeline   │  │    Service   │             │
│  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────┤
│         Spatial Database Backends                │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   PostGIS    │  │ Neo4j Spatial│             │
│  │ (PostgreSQL) │  │   (Graph)    │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
```

### Administrative Level Hierarchy

```
Deutschland (COUNTRY)
├─ Baden-Württemberg (STATE)
│  ├─ Stuttgart (REGIERUNGSBEZIRK)
│  │  ├─ Stuttgart (LANDKREIS)
│  │  │  └─ Stuttgart (GEMEINDE)
│  │  └─ Esslingen (LANDKREIS)
│  │     └─ Esslingen am Neckar (GEMEINDE)
│  └─ ...
└─ Bayern (STATE)
   └─ ...
```

---

## Core Components

### GeoDataType

Supported geographic geometry types:

```python
class GeoDataType(Enum):
    POINT = "point"              # Single coordinate
    POLYGON = "polygon"          # Administrative boundary
    LINESTRING = "linestring"    # Road, route
    MULTIPOINT = "multipoint"    # Multiple locations
    MULTIPOLYGON = "multipolygon"  # Complex boundaries
```

### AdministrativeLevel

German administrative hierarchy:

```python
class AdministrativeLevel(Enum):
    COUNTRY = "country"                 # Deutschland
    STATE = "state"                     # Bundesland
    REGIERUNGSBEZIRK = "regierungsbezirk"  # Administrative district
    LANDKREIS = "landkreis"             # County
    GEMEINDE = "gemeinde"               # Municipality
    ORTSTEIL = "ortsteil"               # District/neighborhood
```

### GeoLocation

Geographic location data class:

```python
@dataclass
class GeoLocation:
    latitude: float               # WGS-84
    longitude: float              # WGS-84
    address: Optional[str]        # Full address
    postal_code: Optional[str]    # PLZ
    city: Optional[str]           # City name
    state: Optional[str]          # Bundesland
    country: str = "Germany"      # Default
    administrative_level: AdministrativeLevel
    confidence: float = 1.0       # Extraction confidence
    source: str                   # "address", "coordinates", etc.
```

---

## Usage Examples

### Automatic Geo Extraction

```python
from api.geo import GeoExtractor

extractor = GeoExtractor()

# Extract locations from document text
document_text = """
Bauantrag für Grundstück in der Hauptstraße 42, 70173 Stuttgart.
Der Antragsteller wohnt in Esslingen am Neckar.
"""

locations = extractor.extract_locations(document_text)
for loc in locations:
    print(f"Found: {loc.address} ({loc.latitude}, {loc.longitude})")
    print(f"Administrative Level: {loc.administrative_level.value}")
    print(f"Confidence: {loc.confidence:.2f}")
```

### Geocoding Addresses

```python
from api.geo import Geocoder

geocoder = Geocoder(provider="nominatim")

# Convert address to coordinates
address = "Marktplatz 1, Stuttgart"
location = geocoder.geocode(address)

if location:
    print(f"Coordinates: {location.latitude}, {location.longitude}")
    print(f"Full Address: {location.address}")
```

### Spatial Queries with PostGIS

```python
from api.geo import PostGISManager

postgis = PostGISManager()

# Find documents within radius
center_lat, center_lon = 48.7758, 9.1829  # Stuttgart
radius_km = 10

documents = postgis.find_documents_within_radius(
    latitude=center_lat,
    longitude=center_lon,
    radius_km=radius_km
)

print(f"Found {len(documents)} documents within {radius_km}km")
```

### Administrative Jurisdiction Detection

```python
from api.geo import AdministrativeResolver

resolver = AdministrativeResolver()

# Determine which municipality a location belongs to
location = GeoLocation(
    latitude=48.7758,
    longitude=9.1829,
    address="Stuttgart"
)

jurisdiction = resolver.get_jurisdiction(location)
print(f"Municipality: {jurisdiction['gemeinde']}")
print(f"Landkreis: {jurisdiction['landkreis']}")
print(f"State: {jurisdiction['state']}")
```

### Neo4j Spatial Relationships

```python
from api.geo import Neo4jSpatialManager

neo4j_spatial = Neo4jSpatialManager()

# Create spatial relationship
neo4j_spatial.create_location_node(
    document_id="doc_12345",
    location=location,
    relationship_type="LOCATED_IN"
)

# Query nearby documents
nearby = neo4j_spatial.find_spatially_near(
    latitude=48.7758,
    longitude=9.1829,
    distance_km=5
)
```

---

## Configuration

### geo_config.json Structure

```json
{
  "geo_settings": {
    "auto_extraction": {
      "enabled": true,
      "quality_threshold": 0.5,
      "max_locations_per_document": 5,
      "extraction_sources": [
        "addresses",
        "postal_codes",
        "place_names",
        "coordinates"
      ]
    },
    "geocoding": {
      "provider": "nominatim",
      "cache_results": true,
      "cache_duration_days": 30,
      "rate_limiting": {
        "requests_per_second": 1
      }
    },
    "spatial_config": {
      "default_srid": 4326,  // WGS-84
      "coordinate_precision": 8,
      "enable_spatial_index": true
    }
  }
}
```

### PostGIS Configuration

```json
{
  "postgis": {
    "backend": "postgresql+postgis",
    "config": {
      "host": "localhost",
      "port": 5432,
      "database": "uds3_geo",
      "sslmode": "prefer"
    },
    "spatial_config": {
      "default_srid": 4326,
      "administrative_data": {
        "load_german_boundaries": true,
        "boundary_sources": [
          "destatis_gem",
          "osm_admin_boundaries"
        ]
      }
    }
  }
}
```

---

## Geo Extraction Pipeline

### Extraction Process

1. **Text Analysis:** Parse document for geographic references
2. **Pattern Matching:** Detect addresses, postal codes, place names
3. **Geocoding:** Convert text to coordinates
4. **Validation:** Verify location plausibility
5. **Administrative Context:** Determine jurisdiction
6. **Storage:** Save to PostGIS + Neo4j

### Extraction Sources

- **Addresses:** Street name + number + postal code
- **Postal Codes:** German PLZ (5 digits)
- **Place Names:** City, municipality, district names
- **Coordinates:** Explicit lat/lon in text
- **Administrative References:** "Gemeinde Stuttgart", "Landkreis Esslingen"

### Quality Thresholds

```python
extraction_config = {
    "quality_threshold": 0.5,      # Min confidence (0-1)
    "require_postal_code": False,   # Stricter validation
    "validate_admin_level": True,   # Check admin hierarchy
    "deduplicate_nearby": True,     # Merge similar locations
    "deduplicate_distance_m": 100   # 100m threshold
}
```

---

## Spatial Query Types

### Distance Queries

```python
# Find documents within radius
results = postgis.within_radius(
    center=(48.7758, 9.1829),
    radius_km=10
)

# Calculate distance between two points
distance_km = postgis.calculate_distance(
    point1=(48.7758, 9.1829),  # Stuttgart
    point2=(48.4011, 9.9876)   # Ulm
)
```

### Containment Queries

```python
# Check if point is within polygon (administrative boundary)
is_in_stuttgart = postgis.point_in_polygon(
    point=(48.7758, 9.1829),
    polygon_id="gemeinde_stuttgart"
)

# Find all documents in a municipality
docs_in_municipality = postgis.documents_in_boundary(
    boundary_type="gemeinde",
    boundary_name="Stuttgart"
)
```

### Proximity Queries

```python
# Find nearest N documents
nearest = postgis.find_nearest_documents(
    location=(48.7758, 9.1829),
    limit=10
)

# Find documents along a route
along_route = postgis.find_along_linestring(
    linestring=[(48.7758, 9.1829), (48.4011, 9.9876)],
    buffer_km=5
)
```

---

## 4D (Temporal-Spatial) Support

### Time + Location Queries

```python
from datetime import datetime, timedelta

# Find documents in Stuttgart during 2024
docs_4d = postgis.query_4d(
    location=(48.7758, 9.1829),
    radius_km=10,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Track location changes over time
location_history = neo4j_spatial.get_location_timeline(
    document_id="doc_12345"
)
```

---

## Administrative Boundaries

### German Boundary Data

UDS3 includes German administrative boundaries from:
- **DESTATIS:** Official statistical office data
- **OpenStreetMap:** Community-maintained boundaries

### Supported Levels

1. **16 Bundesländer** (States)
2. **401 Landkreise & Kreisfreie Städte** (Counties & Independent Cities)
3. **11,000+ Gemeinden** (Municipalities)
4. **Ortsteile** (Districts/Neighborhoods)

### Boundary Queries

```python
# Get all municipalities in a Landkreis
municipalities = resolver.get_municipalities_in_landkreis(
    landkreis_name="Esslingen"
)

# Get administrative hierarchy
hierarchy = resolver.get_full_hierarchy(
    gemeinde="Stuttgart"
)
# Returns: {"gemeinde": "Stuttgart", "landkreis": "Stuttgart", 
#           "regierungsbezirk": "Stuttgart", "state": "Baden-Württemberg"}
```

---

## Performance Characteristics

### Spatial Index Performance

| Query Type | Without Index | With PostGIS Index | Improvement |
|------------|--------------|-------------------|-------------|
| Point-in-polygon | 500-1000ms | 10-50ms | **10-100x** |
| Radius search | 2000ms | 50-100ms | **20-40x** |
| Nearest neighbor | 1000ms | 20-50ms | **20-50x** |

### Geocoding Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Cached geocode | <1ms | From local cache |
| Fresh geocode | 200-500ms | Nominatim API |
| Batch geocoding | 10-20 req/min | Rate limited |

---

## Integration Examples

### Administrative Document Processing

```python
from api.geo import GeoDocumentProcessor

processor = GeoDocumentProcessor()

# Process building permit application
document = {
    "id": "building_permit_2024_001",
    "type": "Baugenehmigung",
    "content": "Bauantrag für Hauptstraße 42, 70173 Stuttgart..."
}

# Extract and enrich with geo data
enriched = processor.process(document)

print(f"Location: {enriched['geo']['primary_location']}")
print(f"Jurisdiction: {enriched['geo']['jurisdiction']}")
print(f"Responsible Authority: {enriched['geo']['authority']}")
```

### Legal Document Geo-Tagging

```python
# Tag court decisions with jurisdiction
legal_doc = {
    "title": "VGH Baden-Württemberg, Urteil vom 15.03.2024",
    "content": "Berufung gegen Baugenehmigung in Esslingen..."
}

geo_tags = extractor.tag_legal_document(legal_doc)
# Returns: {
#   "court_location": "Stuttgart",
#   "case_location": "Esslingen am Neckar",
#   "jurisdiction": "Baden-Württemberg",
#   "administrative_level": "STATE"
# }
```

---

## Dependencies

### Required Libraries

```bash
# Core geo libraries
pip install shapely geopy

# PostGIS support (PostgreSQL + PostGIS extension)
pip install psycopg2-binary

# Optional: Enhanced geocoding
pip install geocoder
```

### Database Requirements

- **PostgreSQL 13+** with PostGIS extension
- **Neo4j 5.0+** with Spatial plugin (optional)

### Coordinate Systems

- **Default:** WGS-84 (SRID 4326) - GPS coordinates
- **Supported:** Any SRID supported by PostGIS
- **German-Specific:** ETRS89/UTM (SRID 25832) for precise mapping

---

## Best Practices

### 1. Always Validate Coordinates

```python
def validate_german_coordinates(lat, lon):
    # Germany bounding box
    if not (47.0 <= lat <= 55.0):
        raise ValueError("Latitude outside Germany")
    if not (5.5 <= lon <= 15.5):
        raise ValueError("Longitude outside Germany")
```

### 2. Cache Geocoding Results

```python
geocoder = Geocoder(
    cache_enabled=True,
    cache_duration_days=30
)
```

### 3. Use Spatial Indexes

```sql
-- Create spatial index in PostGIS
CREATE INDEX idx_documents_location 
ON documents USING GIST (location);
```

### 4. Batch Geocoding

```python
# Process multiple addresses efficiently
addresses = ["Address1", "Address2", ...]
locations = geocoder.batch_geocode(
    addresses,
    rate_limit=1.0  # requests per second
)
```

---

## Troubleshooting

### Geocoding Errors

**Problem:** Geocoding returns None

**Solutions:**
1. Check address format (should include postal code)
2. Verify geocoding provider is reachable
3. Check rate limits
4. Try fallback provider

### PostGIS Connection Issues

**Problem:** Cannot connect to PostGIS database

**Solutions:**
1. Verify PostgreSQL is running
2. Check PostGIS extension is installed: `CREATE EXTENSION postgis;`
3. Verify connection credentials in config
4. Check firewall/network settings

### Incorrect Administrative Level

**Problem:** Wrong jurisdiction detected

**Solutions:**
1. Update boundary data
2. Check coordinate precision
3. Verify SRID matches (should be 4326)
4. Review extraction confidence threshold

---

## Related Documentation

- [4D Geodaten Concept](../UDS3_4D_GEODATEN_VOLLKONZEPT.md) - Full 4D concept
- [Geo Setup Guide](../UDS3_GEODATEN_SETUP_GUIDE.md) - Setup instructions
- [VPB Architecture](../UDS3_VERWALTUNGSARCHITEKTUR.md) - Administrative context

---

## API Reference

### GeoExtractor Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `extract_locations()` | Extract from text | List[GeoLocation] |
| `extract_addresses()` | Find addresses | List[str] |
| `extract_postal_codes()` | Find PLZ | List[str] |
| `extract_coordinates()` | Find lat/lon | List[Tuple] |

### Geocoder Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `geocode()` | Address → coordinates | GeoLocation |
| `reverse_geocode()` | Coordinates → address | str |
| `batch_geocode()` | Multiple addresses | List[GeoLocation] |

### PostGISManager Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `within_radius()` | Radius search | List[Document] |
| `point_in_polygon()` | Containment check | bool |
| `calculate_distance()` | Distance between points | float (km) |
| `find_nearest()` | Nearest neighbors | List[Document] |

---

**Last Updated:** November 17, 2025  
**Version:** 1.5.0  
**Status:** Production Ready ✅  
**Geographic Coverage:** Germany (primarily), expandable

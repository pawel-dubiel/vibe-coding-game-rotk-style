# Tile Terrain Generator Tests

This directory contains comprehensive tests for the `tools/tile_terrain_generator.py` module.

## Test Structure

### `test_tile_terrain_generator.py` - Unit Tests
- **TestGeographicBounds**: Tests for geographic boundary data structure
- **TestMapTileFetcher**: Tests for map tile fetching and coordinate conversion
  - Coordinate transformations (deg2num, num2deg, roundtrip accuracy)
  - Tile fetching with success/failure scenarios
  - Area tile stitching logic
- **TestTileTerrainClassifier**: Tests for terrain classification from pixel colors
  - Color distance calculations
  - Terrain type classification for all supported types
  - Predefined color matching
- **TestMedievalCityFunctions**: Tests for city data loading and filtering
  - JSON file loading with error handling
  - Geographic boundary filtering
  - Malformed data handling
- **TestRectangleMerging**: Tests for terrain rectangle optimization
  - Horizontal rectangle merging
  - Complex adjacent rectangle merging
  - Edge cases and empty inputs
- **TestExportToJson**: Tests for JSON export functionality
  - Basic export structure validation
  - Terrain grouping verification
- **TestCoordinateConversions**: Tests for city coordinate mapping
  - Basic coordinate conversion
  - Collision detection and resolution
  - City income and specialization calculation
- **TestIntegrationScenarios**: Combined workflow tests
  - Water city relocation to land
  - Full workflow with mocked dependencies

### `test_integration.py` - Integration Tests
- **TestFullWorkflowIntegration**: End-to-end workflow tests
  - Complete tile-to-JSON generation pipeline
  - Terrain diversity handling
  - Main function execution with various parameters
  - City processing integration with terrain
  - Coordinate system consistency validation
  - Large map performance testing
  - Edge case geographic bounds
- **TestErrorHandling**: Error scenario testing
  - Corrupt image data handling
  - Missing cities file scenarios
  - Malformed city data processing

### `test_performance.py` - Performance & Stress Tests
- **TestPerformance**: Performance benchmarks
  - Terrain classification speed (10k pixels < 1s)
  - Rectangle merging efficiency
  - Large city list processing
  - Color distance calculation speed
- **TestMemoryUsage**: Memory efficiency tests
  - Large terrain map memory patterns
  - Rectangle merging memory reduction
  - Coordinate calculation memory leaks
- **TestScalability**: Scalability validation
  - Zoom level scaling behavior
  - Hex grid size scaling
  - City collision resolution scaling
- **TestStressTests**: Edge case and stress scenarios
  - Extreme color value handling
  - Maximum rectangle merging scenarios
  - Very large coordinate values
  - Empty input handling

## Key Test Coverage

### Core Functionality
- ✅ Geographic coordinate transformations
- ✅ Map tile fetching and stitching  
- ✅ Terrain classification from map colors
- ✅ City data processing and placement
- ✅ Rectangle merging optimization
- ✅ JSON export with proper structure

### Error Handling
- ✅ Network failures during tile fetching
- ✅ Malformed input data
- ✅ Missing files
- ✅ Invalid coordinates
- ✅ Extreme input values

### Performance
- ✅ Classification speed benchmarks
- ✅ Memory usage patterns
- ✅ Scalability with different input sizes
- ✅ Rectangle merging efficiency

### Integration
- ✅ End-to-end workflow validation
- ✅ Component interaction testing
- ✅ Real-world scenario simulation

## Running the Tests

```bash
# Run all tile generator tests
python -m pytest tests/tools/tile_generator/ -v

# Run specific test files
python -m pytest tests/tools/tile_generator/test_tile_terrain_generator.py -v
python -m pytest tests/tools/tile_generator/test_integration.py -v
python -m pytest tests/tools/tile_generator/test_performance.py -v

# Run with coverage
python -m pytest tests/tools/tile_generator/ --cov=tools.tile_terrain_generator

# Run performance tests only
python -m pytest tests/tools/tile_generator/test_performance.py::TestPerformance -v
```

## Test Statistics

- **Total Tests**: 66
- **Unit Tests**: 40
- **Integration Tests**: 17
- **Performance Tests**: 9
- **All Tests Pass**: ✅

## Dependencies

The tests use the following key libraries:
- `pytest` - Test framework
- `unittest.mock` - Mocking for external dependencies
- `PIL (Pillow)` - Image processing (mocked in tests)
- `tempfile` - Temporary file handling for exports

## Regression Testing

These tests serve as regression protection for the tile terrain generator, ensuring that:
1. Map tile fetching continues to work reliably
2. Terrain classification remains accurate
3. City placement logic handles edge cases
4. Performance characteristics are maintained
5. Export format stays compatible with the game

The tests are designed to be fast, isolated, and comprehensive to support continuous integration and development workflows.
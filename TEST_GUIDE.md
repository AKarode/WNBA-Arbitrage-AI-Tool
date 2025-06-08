# WNBA Arbitrage AI Tool - Testing Guide

## 🧪 Comprehensive Test Suite

This guide covers running and understanding the complete test suite for the WNBA Arbitrage AI Tool.

---

## 📋 Test Structure

### Test Files Overview
```
tests/
├── conftest.py                 # Global fixtures and configuration
├── pytest.ini                 # Pytest configuration
├── test_config.py             # Configuration module tests
├── test_multi_source_api.py    # Multi-source API endpoint tests
├── test_data_ingestion.py      # Data ingestion component tests
├── test_integration.py         # End-to-end integration tests
└── test_main.py               # Basic API tests (existing)
```

### Test Categories
- 🔧 **Unit Tests**: Individual component testing
- 🔗 **Integration Tests**: End-to-end workflow testing
- 🌐 **API Tests**: REST endpoint testing
- ⚡ **Performance Tests**: Speed and load testing
- 🛡️ **Security Tests**: Input validation and error handling

---

## 🚀 Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt

# Ensure Redis is available (for rate limiting tests)
# Option 1: Local Redis
brew install redis && brew services start redis

# Option 2: Use mock Redis (tests will automatically mock if Redis unavailable)
```

### Basic Test Execution

#### Run All Tests
```bash
# Run complete test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m api
```

#### Run Specific Test Files
```bash
# Test multi-source API
pytest tests/test_multi_source_api.py -v

# Test data ingestion
pytest tests/test_data_ingestion.py -v

# Test integration workflows
pytest tests/test_integration.py -v

# Test configuration
pytest tests/test_config.py -v
```

#### Run Specific Test Classes or Functions
```bash
# Test specific class
pytest tests/test_multi_source_api.py::TestMultiSourceOddsEndpoints -v

# Test specific function
pytest tests/test_data_ingestion.py::TestRateLimitManager::test_rate_limiter_initialization -v
```

### Advanced Test Options

#### Performance Testing
```bash
# Run only performance tests
pytest -m performance -v

# Skip slow tests
pytest -m "not slow"

# Run with timing information
pytest --durations=10
```

#### Parallel Testing
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run on 4 cores
pytest -n 4
```

#### Test Selection
```bash
# Run tests matching pattern
pytest -k "test_arbitrage"

# Run integration tests only
pytest -m integration

# Run API tests excluding slow ones
pytest -m "api and not slow"
```

---

## 📊 Test Coverage

### Generate Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Generate terminal coverage report
pytest --cov=app --cov-report=term-missing

# Generate XML coverage (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Targets
- **Overall Coverage**: >90%
- **Critical Components**: >95%
  - Data ingestion modules
  - Arbitrage detection logic
  - API endpoints
- **Configuration**: >85%

### View Coverage Report
```bash
# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 🧩 Test Categories Detail

### 1. Unit Tests (`-m unit`)
Test individual components in isolation.

#### Rate Limiting Tests
```bash
pytest tests/test_data_ingestion.py::TestRateLimitManager -v
```
- Tests Redis integration
- Validates rate limit enforcement
- Error handling for Redis failures

#### Data Source Tests
```bash
pytest tests/test_data_ingestion.py::TestEnhancedOddsAPI -v
pytest tests/test_data_ingestion.py::TestBovadaScraper -v
```
- API integration testing
- Scraping functionality
- Data normalization

#### Configuration Tests
```bash
pytest tests/test_config.py -v
```
- Configuration validation
- Environment-specific settings
- Parameter validation functions

### 2. API Tests (`-m api`)
Test REST API endpoints and responses.

#### Multi-Source Endpoints
```bash
pytest tests/test_multi_source_api.py::TestMultiSourceOddsEndpoints -v
```
- Odds retrieval from multiple sources
- Response format validation
- Error handling

#### Arbitrage Detection Endpoints
```bash
pytest tests/test_multi_source_api.py::TestArbitrageEndpoints -v
```
- Real-time arbitrage detection
- Market summary generation
- Execution simulation

### 3. Integration Tests (`-m integration`)
Test complete workflows end-to-end.

#### Complete Arbitrage Workflow
```bash
pytest tests/test_integration.py::TestEndToEndWorkflows::test_complete_arbitrage_detection_workflow -v
```
- Data collection → Processing → Detection → Alerts
- Multi-source coordination
- Real-time updates

#### Error Recovery Testing
```bash
pytest tests/test_integration.py::TestEndToEndWorkflows::test_error_recovery_workflow -v
```
- Source failure handling
- System recovery
- Graceful degradation

### 4. Performance Tests (`-m performance`)
Validate system performance under load.

#### Concurrent Request Testing
```bash
pytest tests/test_integration.py::TestPerformanceIntegration::test_concurrent_request_handling -v
```
- Multiple simultaneous API calls
- Resource usage validation
- Response time requirements

#### Large Dataset Processing
```bash
pytest tests/test_integration.py::TestPerformanceIntegration::test_large_dataset_performance -v
```
- Processing 100+ games
- Memory usage optimization
- Arbitrage detection speed

---

## 🔧 Test Environment Setup

### Environment Variables
```bash
# Required for testing
export ENVIRONMENT=testing
export REDIS_URL=redis://localhost:6379/15
export ODDS_API_KEY=test_api_key_for_testing

# Optional for enhanced testing
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Mock vs Real Services

#### Redis Testing
```bash
# Use real Redis (recommended for integration tests)
pytest tests/test_data_ingestion.py -m redis

# Use mock Redis (faster, for unit tests)
pytest tests/test_data_ingestion.py -m "not redis"
```

#### External API Testing
```bash
# All external APIs are mocked by default
# To test with real APIs (requires API keys):
export TEST_WITH_REAL_APIS=true
pytest tests/test_data_ingestion.py::TestEnhancedOddsAPI::test_get_wnba_odds_success
```

### Database Testing
```bash
# Tests use mock database by default
# For future database integration tests:
export TEST_DATABASE_URL=postgresql://test:test@localhost/test_wnba_arbitrage
```

---

## 🐛 Debugging Tests

### Debug Mode
```bash
# Run with Python debugger
pytest --pdb

# Drop into debugger on failures only
pytest --pdb-failures

# Capture output (useful for debugging prints)
pytest -s
```

### Verbose Logging
```bash
# Enable debug logging during tests
pytest --log-cli-level=DEBUG

# Log to file
pytest --log-file=test.log --log-file-level=DEBUG
```

### Test Isolation
```bash
# Run single test with maximum verbosity
pytest tests/test_multi_source_api.py::TestMultiSourceOddsEndpoints::test_get_multi_source_current_odds_success -vvv -s
```

---

## 📈 Continuous Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🎯 Test Data and Fixtures

### Using Test Fixtures
Tests use shared fixtures from `conftest.py`:

```python
# Example test using fixtures
def test_arbitrage_detection(sample_odds_data, sample_arbitrage_opportunity):
    # Test logic here
    assert len(sample_odds_data) > 0
    assert sample_arbitrage_opportunity.profit_percentage > 0
```

### Creating Custom Test Data
```python
# Use data generators
def test_custom_scenario(odds_data_generator, arbitrage_opportunity_generator):
    odds = odds_data_generator(
        home_team="Custom Team",
        away_team="Other Team",
        home_price=-130,
        away_price=120
    )
    # Test with custom data
```

### Mock Configuration
```python
# Override configuration for testing
@patch('app.config.data_sources.DATA_SOURCES')
def test_with_custom_config(mock_config):
    mock_config['test_source'] = SourceConfig(...)
    # Test with custom configuration
```

---

## 🚨 Common Issues and Solutions

### Issue: Redis Connection Error
```bash
# Error: redis.exceptions.ConnectionError
# Solution 1: Start Redis
brew services start redis

# Solution 2: Use mock Redis (automatic in tests)
pytest -m "not redis"
```

### Issue: Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Async Test Warnings
```bash
# Warning: RuntimeWarning: coroutine was never awaited
# Solution: Tests already configured with pytest-asyncio
# Ensure test functions are marked with @pytest.mark.asyncio
```

### Issue: Selenium WebDriver Not Found
```bash
# Error: selenium.common.exceptions.WebDriverException
# Solution: Install ChromeDriver
brew install chromedriver  # macOS
sudo apt-get install chromium-chromedriver  # Ubuntu

# Or use webdriver-manager (automatic)
pip install webdriver-manager
```

### Issue: Rate Limiting in Tests
```bash
# Tests may fail due to rate limiting
# Solution: Tests use mock rate limiter by default
# For real rate limiting tests, clear Redis:
redis-cli FLUSHDB
```

---

## 📋 Test Checklist

### Before Committing
- [ ] All tests pass: `pytest`
- [ ] Coverage above 90%: `pytest --cov=app`
- [ ] No linting errors: `flake8 app tests`
- [ ] Code formatted: `black app tests`
- [ ] Integration tests pass: `pytest -m integration`

### Before Deployment
- [ ] Performance tests pass: `pytest -m performance`
- [ ] Security tests pass: `pytest -m security`
- [ ] Load tests completed
- [ ] Error handling validated
- [ ] Documentation updated

### Release Testing
- [ ] End-to-end workflows tested
- [ ] Real API integration tested (staging)
- [ ] Database migrations tested
- [ ] Monitoring and alerts tested
- [ ] Rollback procedures tested

---

## 📞 Getting Help

### Test Documentation
- 📖 **Pytest Docs**: https://docs.pytest.org/
- 🔧 **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- 🧪 **Async Testing**: https://pytest-asyncio.readthedocs.io/

### Debugging Resources
```bash
# Get help on pytest options
pytest --help

# List all available markers
pytest --markers

# List all fixtures
pytest --fixtures

# Collect tests without running
pytest --collect-only
```

### Contributing Tests
1. **Add test for new features**: Every new feature needs tests
2. **Follow naming convention**: `test_feature_scenario`
3. **Use appropriate markers**: `@pytest.mark.api`, `@pytest.mark.slow`, etc.
4. **Document complex tests**: Add docstrings for integration tests
5. **Mock external services**: Keep tests fast and reliable

---

**Status**: Comprehensive test suite ready for WNBA 2025 season! 🧪✅
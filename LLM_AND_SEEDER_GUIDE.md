# LLM Provider Selection & Stock Exchange Seeder - Implementation Guide

## Overview
This guide covers the new LLM provider selection feature, stock exchange seeding, and improved exception handling for the FinTech Sales Intelligence platform.

---

## Part 1: LLM Provider Selection

### What Was Done
The application now supports **easy LLM provider switching** with full validation and error handling.

### Supported LLM Providers
- **OpenAI** (GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo)
- **DeepSeek** (deepseek-chat, deepseek-coder)
- **Qwen** (qwen-plus, qwen-turbo, qwen-long)
- **Ollama** (llama3, llama2, mistral - local)
- **Gemini** (gemini-2.5-flash, gemini-2.0-pro)

### Configuration (`.env`)
```bash
# Select your LLM provider
LLM_PROVIDER=openai

# Configure API keys for each provider you plan to use
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here
QWEN_API_KEY=sk-your-key-here
GEMINI_API_KEY=sk-your-key-here

# Ollama runs locally, no API key needed
OLLAMA_BASE_URL=http://localhost:11434/v1
```

### Exception Handling
The application now handles **all LLM-related errors gracefully**:

#### Missing API Key Error
```json
{
  "error": "LLM Configuration Error",
  "message": "API Key Invalid or Missing for OpenAI.",
  "details": "Please configure the required API key in .env and restart the application."
}
```

#### Quota/Rate Limit Error
```json
{
  "error": "LLM Configuration Error",
  "message": "Quota Exceeded or Rate Limit Hit for OpenAI.",
  "details": "Please check your API usage and limits."
}
```

### Exception Handler Code
In `app/presentation/api/main.py`, the `@app.exception_handler(ValueError)` catches all LLM errors:

```python
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError from LLM clients (e.g., missing API keys)."""
    error_msg = str(exc)
    logger.warning(f"Validation error: {error_msg}")
    
    # Check if it's an API key or auth error
    if any(keyword in error_msg.lower() for keyword in ["api key", "unauthorized", "401", "auth"]):
        return JSONResponse(
            status_code=401,
            content={
                "error": "LLM Configuration Error",
                "message": error_msg,
                "details": "Please configure the required API key in .env and restart the application."
            }
        )
    
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "message": error_msg}
    )
```

### LLM Factory Enhancement
The `LLMFactory` class now provides:

1. **available_providers()** - Returns list of all providers with configuration status
2. **create_for_provider_name(provider_name)** - Create client by string name

```python
# Get all providers
providers = LLMFactory.available_providers()
# Returns:
# [
#   {"value": "openai", "label": "OpenAI", "configured": true, "model": "gpt-4o"},
#   {"value": "deepseek", "label": "DeepSeek", "configured": false, "warning": "..."},
#   ...
# ]

# Create client by provider name (from UI dropdown)
client = LLMFactory.create_for_provider_name("deepseek")
```

---

## Part 2: Stock Exchange Seeder

### What Was Included
A comprehensive seeder with **19 major stock exchanges** across regions:

#### Geographic Coverage
- **North America**: NYSE, NASDAQ, TSX
- **Europe**: LSE, Euronext Paris, Deutsche Börse, SIX Swiss, Borsa Italiana, BME
- **Asia-Pacific**: TSE, HKEX, SSE, SGX, NSE, ASX
- **Latin America**: B3, BVC
- **Middle East**: TADAWUL, Nasdaq Dubai

### Seed Data Structure
Each exchange includes:
- **name**: Exchange full name
- **country**: Country of operation
- **website_url**: Official website
- **member_list_url**: Member/broker list URL
- **total_members**: Number of members/brokers

### Database Schema
Stock exchanges are stored in the `exchanges` table (already defined in models.py):

```python
class ExchangeModel(Base):
    __tablename__ = "exchanges"
    
    id = Column(String(36), primary_key=True)  # UUID as string (MySQL compatible)
    name = Column(String(500), nullable=False, index=True)
    country = Column(String(200), nullable=True)
    website_url = Column(Text, nullable=True)
    member_list_url = Column(Text, nullable=True)
    total_members = Column(Integer, default=0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### Seeder Location
File: `app/infrastructure/database/seeders.py`

**Key Functions:**
- `seed_stock_exchanges(session)` - Seeds DB with initial exchange data
- `get_countries_list()` - Returns unique countries (for dropdowns)
- `get_llm_models_for_provider(provider)` - Returns available models per provider

### Seeding Trigger
The seeder runs **automatically on app startup** when:
- `DB_INIT=true` is set in `.env` (for first deploy)
- OR `APP_DEBUG=true` is set

In `app/presentation/api/main.py`:
```python
if get_settings().app_debug or get_settings().db_init:
    await db_manager.create_tables()
    # Seed initial data
    async with db_manager.get_session() as session:
        await seed_stock_exchanges(session)
```

---

## Part 3: UI Enhancements

### New Dropdowns

#### 1. LLM Provider Selector
- **Endpoint**: `GET /api/v1/config/llm-providers`
- **Returns**: List of providers with configuration status
- **Warning**: Shows if API key is missing

#### 2. LLM Model Selector
- **Endpoint**: `GET /api/v1/config/llm-models/{provider}`
- **Updates**: When provider changes
- **Returns**: List of available models for selected provider

#### 3. Country Selector
- **Endpoint**: `GET /api/v1/config/countries`
- **Returns**: Unique countries from seeded exchanges

#### 4. Stock Exchange Selector
- **Endpoint**: `GET /api/v1/exchanges?country={country}`
- **Updates**: When country changes
- **Returns**: Exchanges for selected country with member counts

### Form Layout
The analysis form now has **4 sections**:

```
Row 1: [LLM Provider Dropdown] [Model Dropdown]
Row 2: [Country Dropdown] [Exchange Dropdown]
Row 3: [Custom Exchange Input (optional)]
Button: Start Analysis
```

### Updated HTML
File: `app/presentation/static/index.html`

New form structure:
```html
<form id="analysis-form" class="analysis-form">
    <!-- LLM & Model Selection -->
    <div class="form-row">
        <div class="input-group">
            <label for="llm-provider">LLM Provider</label>
            <select id="llm-provider" class="form-select">...</select>
            <small id="llm-warning" class="warning-text"></small>
        </div>
        <div class="input-group">
            <label for="llm-model">Model</label>
            <select id="llm-model" class="form-select">...</select>
        </div>
    </div>
    
    <!-- Exchange & Country Selection -->
    <div class="form-row">
        <div class="input-group">
            <label for="country">Country</label>
            <select id="country" class="form-select">...</select>
        </div>
        <div class="input-group">
            <label for="exchange-list">Stock Exchange</label>
            <select id="exchange-list" class="form-select">...</select>
        </div>
    </div>
    
    <!-- Custom Exchange Option -->
    <div class="input-group full-width">
        <label for="exchange-name">Or Enter Custom Exchange</label>
        <input type="text" id="exchange-name" placeholder="...">
    </div>
    
    <button type="submit" class="btn btn-primary">Start Analysis</button>
</form>
```

### Updated CSS
File: `app/presentation/static/css/styles.css`

New styles for form layout:
```css
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

select {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-glass);
    padding: 12px 16px;
    border-radius: 8px;
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,...");
}

.warning-text {
    color: var(--accent-rose);
    font-size: 0.8rem;
}
```

### Updated JavaScript
File: `app/presentation/static/js/app.js`

**Key additions:**
- `loadLLMProviders()` - Fetch and populate LLM dropdown
- `loadModelsForProvider(provider)` - Fetch models for selected provider
- `loadCountries()` - Fetch countries from seeder
- `loadExchangesForCountry(country)` - Fetch exchanges for selected country
- Event listeners for dropdown interactions

```javascript
// Load providers on page load
await loadLLMProviders();
await loadCountries();

// Update models when provider changes
llmProviderSelect.addEventListener('change', (e) => {
    loadModelsForProvider(e.target.value);
});

// Load exchanges when country changes
countrySelect.addEventListener('change', (e) => {
    loadExchangesForCountry(e.target.value);
});

// Auto-fill exchange name from list
exchangeListSelect.addEventListener('change', (e) => {
    exchangeInput.value = e.target.value;
});
```

---

## Part 4: API Endpoints

### Configuration Endpoints

#### Get LLM Providers
```bash
GET /api/v1/config/llm-providers
```

Response:
```json
[
  {
    "value": "openai",
    "label": "OpenAI",
    "configured": true,
    "model": "gpt-4o",
    "available_models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
  },
  {
    "value": "deepseek",
    "label": "DeepSeek",
    "configured": false,
    "warning": "API key not configured. Set DEEPSEEK_API_KEY in .env"
  }
]
```

#### Get Models for Provider
```bash
GET /api/v1/config/llm-models/openai
```

Response:
```json
{
  "provider": "openai",
  "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
}
```

#### Get Countries
```bash
GET /api/v1/config/countries
```

Response:
```json
{
  "countries": ["Australia", "Brazil", "Canada", "China", ..., "United States"]
}
```

#### Check LLM Status
```bash
GET /api/v1/config/llm-status?provider=openai
```

Response:
```json
{
  "provider": "openai",
  "configured": true,
  "model": "gpt-4o",
  "status": "ready"
}
```

### Exchange Endpoints

#### List Exchanges (with filters)
```bash
GET /api/v1/exchanges?country=United%20States&skip=0&limit=50
```

Response:
```json
{
  "exchanges": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "New York Stock Exchange (NYSE)",
      "country": "United States",
      "website_url": "https://www.nyse.com",
      "member_list_url": "https://www.nyse.com/about/memberships",
      "total_members": 2400,
      "status": "active"
    }
  ],
  "count": 2,
  "skip": 0,
  "limit": 50
}
```

#### Get Exchanges by Country
```bash
GET /api/v1/exchanges/United%20States
```

#### Search Exchanges
```bash
GET /api/v1/exchanges-search?query=york
```

---

## Testing

### 1. Test LLM Provider Switching

```bash
# Test with OpenAI (if configured)
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "exchange_name": "NYSE",
    "llm_provider": "openai",
    "llm_model": "gpt-4o"
  }'

# Test with missing API key (should return 401)
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "exchange_name": "NYSE",
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat"
  }'
# Expected response: 401 Unauthorized with "LLM Configuration Error"
```

### 2. Test Stock Exchange Seeder

```bash
# Verify seeding
curl http://localhost:8000/api/v1/exchanges

# Filter by country
curl "http://localhost:8000/api/v1/exchanges?country=United%20States"

# Get countries
curl http://localhost:8000/api/v1/config/countries

# Search exchanges
curl "http://localhost:8000/api/v1/exchanges-search?query=stock"
```

### 3. Test UI Dropdowns

Open `http://localhost:8000` and verify:
- [ ] LLM provider dropdown loads all providers
- [ ] "✓" shows next to configured providers
- [ ] Warning text appears for unconfigured providers
- [ ] Models load when provider is selected
- [ ] Countries load on page load
- [ ] Exchanges load when country is selected
- [ ] Exchange name auto-fills when exchange is selected from list

---

## Configuration Changes

### `.env.example` (already updated)
```bash
DB_INIT=true  # Enable table/seed creation on startup (disable after first run)
```

### `pyproject.toml` (already updated)
- `asyncmy>=0.8.0` - MySQL async driver (replaced asyncpg)

### `docker-compose.yml` (already updated)
- MySQL service (replaced PostgreSQL)
- Adminer instead of pgAdmin

### `render.yaml` (already updated)
- Added `DB_INIT=true` for first deploy
- Uses `$PORT` environment variable

---

## File Changes Summary

### New Files
1. `app/infrastructure/database/seeders.py` - Seeder logic with 19 exchanges
2. `app/presentation/api/routers/config_router.py` - LLM & config endpoints
3. `app/presentation/api/routers/exchanges_router.py` - Exchange search/filter endpoints

### Modified Files
1. `app/presentation/api/main.py` - Added routers, seeder call, exception handlers
2. `app/shared/config/settings.py` - Added `db_init` setting
3. `app/presentation/static/index.html` - New form dropdowns
4. `app/presentation/static/css/styles.css` - Form styling
5. `app/presentation/static/js/app.js` - Dropdown logic
6. `app/presentation/api/routers/analysis_router.py` - Removed duplicate `/llm-providers` endpoint

---

## Deployment Checklist

### Before First Deploy
- [ ] Set `LLM_PROVIDER=openai` (or your choice) in `.env`
- [ ] Add `OPENAI_API_KEY` (or corresponding provider key) to `.env`
- [ ] Set `DATABASE_URL` to MySQL instance (PlanetScale, RDS, etc.)
- [ ] Set `REDIS_URL` to Redis instance
- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Set `DB_INIT=true` to create tables and seed exchanges on first startup

### On Render Dashboard
1. Create new Web Service (Docker)
2. Connect your Git repository
3. Set all secrets from `.env` in Render dashboard
4. Deploy!
5. After first successful deploy, set `DB_INIT=false` in Render secrets

---

## FAQ

### Q: Can I switch LLM providers after deployment?
**A:** Yes! Update `LLM_PROVIDER` in `.env` (or Render secrets) and restart the app. The new provider will be used for all analyses.

### Q: What if my API key is invalid?
**A:** The app will return a 401 error with a clear message. Check your API key in `.env` and restart.

### Q: Can I add more stock exchanges to the seeder?
**A:** Yes! Edit `STOCK_EXCHANGES_SEED_DATA` in `app/infrastructure/database/seeders.py` and re-run the seeder (set `DB_INIT=true`).

### Q: Why String(36) for UUIDs instead of UUID type?
**A:** MySQL doesn't have native UUID support like PostgreSQL. String(36) stores UUIDs as text (e.g., `550e8400-e29b-41d4-a716-446655440000`).

### Q: Does Render support MySQL?
**A:** Render doesn't offer managed MySQL. Use external providers like PlanetScale, AWS RDS, Google Cloud SQL, or DigitalOcean.

---

## Next Steps

1. **Test LLM switching** - Verify all providers work with your API keys
2. **Deploy to Render** - Push the `mysql-render` branch and create a deployment
3. **Monitor logs** - Watch for any API key or connection errors
4. **Add more exchanges** - Customize seeder data for your target regions
5. **Customize models** - Update model lists in `get_llm_models_for_provider()` for each provider

---

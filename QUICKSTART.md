# Quick Start Guide

Get the Estate Crawler running in 5 minutes.

## Installation (One-time)

### Option A: Automated Setup (Recommended)

```bash
cd /root/clawd/EstatePredictor
bash setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Initialize database
- Run tests
- Create .env file

### Option B: Manual Setup

```bash
cd /root/clawd/EstatePredictor

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python main.py init

# Create config file
cp .env.example .env
```

## Running the Crawler

### 1. One-Time Scrape

```bash
# Activate environment
source venv/bin/activate

# Run scraper
python main.py scrape

# Scrape and export
python main.py scrape --export
```

### 2. Automated Scheduling

```bash
# Start scheduler (runs every 2 days by default)
python main.py scheduler

# Keep it running in background
nohup python main.py scheduler > logs/scheduler.log 2>&1 &
```

### 3. Export Data

```bash
# Export all formats (CSV, JSON, Parquet)
python main.py export --format all

# Export only CSV
python main.py export --format csv

# Export ML dataset
python main.py export --format ml

# Export statistics
python main.py export --format stats
```

## Docker Usage

### Quick Start with Docker

```bash
# Build image
docker build -t estate-crawler:latest .

# Run container
docker run -d \
  -v estate-data:/app/data \
  -v estate-logs:/app/logs \
  -e SCHEDULER_ENABLED=True \
  --name estate-crawler \
  estate-crawler:latest

# View logs
docker logs -f estate-crawler

# Stop container
docker stop estate-crawler
```

### Using Docker Compose

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## View Results

### Check Database

```bash
# Show statistics
python main.py stats

# Or inspect directly
sqlite3 data/estate_crawler.db "SELECT COUNT(*) FROM properties;"
```

### Check Logs

```bash
# View recent logs
tail -f logs/estate_crawler.log

# Search for errors
grep ERROR logs/estate_crawler.log
```

### Browse Exported Data

```bash
# List exported files
ls -lh data/processed/

# Preview CSV
head -20 data/processed/estate_data_*.csv

# Preview JSON
python -m json.tool data/processed/estate_data_*.json | head -50
```

## Configuration

Quick config changes in `.env`:

```bash
# Edit config
nano .env

# Set scraping interval (in hours)
SCHEDULER_INTERVAL_HOURS=24

# Set log level
LOG_LEVEL=DEBUG  # For troubleshooting

# Set request timeout (in seconds)
REQUEST_TIMEOUT=60
```

## Testing

```bash
# Run all tests
python test_scraper.py

# Run specific test
python test_scraper.py TestDatabase.test_insert_property

# Run with pytest
pytest test_scraper.py -v
```

## Troubleshooting

### "No module named 'X'"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database locked
```bash
# Reset database
rm data/estate_crawler.db
python main.py init
```

### Port already in use (for dashboard, if added)
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Check if scraper is running

```bash
# Check process
ps aux | grep python | grep scraper

# Check for active jobs
python -c "from database import EstateDatabase; db = EstateDatabase(); print(db.get_stats())"
```

## Common Commands

```bash
# Initialize everything
python main.py init

# Scrape once
python main.py scrape

# Scrape and immediately export
python main.py scrape --export

# Start background scheduler
nohup python main.py scheduler &

# Export all data
python main.py export --format all

# Show statistics
python main.py stats

# Run tests
python test_scraper.py

# View help
python main.py --help
```

## File Locations

- **Database**: `data/estate_crawler.db`
- **Logs**: `logs/estate_crawler.log`
- **Exports**: `data/processed/`
- **Config**: `.env`
- **Code**: `.py` files in root

## Next Steps

1. **Monitor**: Watch `logs/estate_crawler.log` while running
2. **Analyze**: Export data and explore in spreadsheet
3. **Extend**: Add more domains by following DEVELOPMENT.md
4. **Deploy**: Use Docker Compose for production

## Help

- **General Issues**: Check README.md
- **Development**: Read DEVELOPMENT.md
- **Error Messages**: Check logs/estate_crawler.log
- **Code Examples**: See test_scraper.py

---

**Happy scraping!** 🚀

# 📡 API Reference

## Hevy API Integration

This tool integrates with the [Hevy API](https://api.hevyapp.com/docs/) to fetch and analyze your workout data.

## API Requirements

- **Hevy Pro Subscription**: Required for API access
- **API Key**: Generated from [Hevy Developer Settings](https://hevy.com/settings?developer=)
- **Rate Limits**: Hevy API has rate limiting (tool handles this automatically)

## Endpoints Used

### `/v1/workouts/events`

**Purpose**: Fetch workout events and exercise data

**Parameters**:
- `page`: Page number (default: 1)
- `pageSize`: Items per page (max: 10, default: 10)
- `since`: ISO date string (default: 30 days ago)

**Example Request**:
```
GET https://api.hevyapp.com/v1/workouts/events?page=1&pageSize=10&since=2024-01-01T00:00:00Z
```

**Response Structure**:
```json
{
  "events": [
    {
      "type": "updated",
      "workout": {
        "id": "workout-id",
        "title": "Push Day",
        "start_time": "2024-01-15T10:00:00Z",
        "exercises": [
          {
            "title": "Bench Press",
            "sets": [
              {
                "type": "normal",
                "weight_kg": 80.0,
                "reps": 8,
                "rpe": 8.5,
                "index": 1
              }
            ]
          }
        ]
      }
    }
  ],
  "page": 1,
  "page_count": 5
}
```

## Data Processing Flow

1. **Fetch**: Tool calls API to get recent workout events
2. **Clean**: Removes null values to reduce file size
3. **Transform**: Converts JSON to pandas DataFrame
4. **Filter**: 
   - Limits to last 90 days
   - Excludes warm-ups, cardio, etc.
   - Focuses on strength training exercises
5. **Analyze**: Runs comprehensive coaching algorithms

## Authentication

```python
headers = {
    "api-key": "your-hevy-api-key",
    "Content-Type": "application/json"
}
```

## Error Handling

The tool handles common API issues:

- **401 Unauthorized**: Invalid or missing API key
- **429 Rate Limited**: Automatic retry with backoff
- **500 Server Error**: Graceful failure with user message
- **Network Issues**: Connection timeout handling

## Data Privacy

- **Local Storage**: All data is stored locally on your machine
- **No External Sharing**: Tool never sends your data to third parties
- **Optional Deletion**: Generated files can be safely deleted
- **API Key Security**: Stored in `.env` file (not committed to git)

## Pagination

The tool automatically handles pagination:

```python
def get_all_recent_workouts(self, days: int = 30):
    all_events = []
    page = 1
    
    while True:
        data = self.get_workout_events(page=page, pageSize=10, since=since)
        events = data.get("events", [])
        
        if not events:
            break
            
        all_events.extend(events)
        page += 1
    
    return all_events
```

## API Limits & Best Practices

1. **Page Size**: Maximum 10 items per request
2. **Date Range**: Fetch only what you need (default: 30 days)
3. **Caching**: Tool saves data locally to avoid unnecessary API calls
4. **Respect Limits**: Built-in rate limiting protection

## Troubleshooting API Issues

### Invalid API Key
```
❌ Error: HEVY_API_KEY environment variable not set
```
**Solution**: Check your `.env` file and verify API key

### No Data Returned
```
❌ No workout events found
```
**Solution**: 
- Ensure you have workouts in Hevy
- Try increasing days: `--days 90`
- Check your Hevy Pro subscription status

### Rate Limited
```
❌ Error fetching workout events: 429 Too Many Requests
```
**Solution**: Tool handles this automatically with retries

## Example Usage

```bash
# Fetch last 7 days only
python hevy_stats.py fetch --days 7

# Fetch and analyze last 30 days
python hevy_stats.py both --days 30

# Use custom file names
python hevy_stats.py fetch --outfile my_workouts.json
python hevy_stats.py analyze --infile my_workouts.json
```

## Related Links

- [Official Hevy API Documentation](https://api.hevyapp.com/docs/)
- [Hevy Developer Settings](https://hevy.com/settings?developer=)
- [Hevy App](https://hevy.com) 
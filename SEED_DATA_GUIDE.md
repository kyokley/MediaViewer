# Seed Data Command Documentation

## Overview

The `seed_data` management command generates sample data for testing the MediaViewer SPA application. It creates test users, movies, TV shows, genres, requests, comments, and video progress entries.

## Features

### Data Generated

- **Test Users** (3 users)
  - `admin` (superuser, password: admin)
  - `test_user` (regular user, password: password)
  - `demo_user` (regular user, password: password)

- **Genres** (10 genres)
  - Action, Comedy, Drama, Horror, Science Fiction, Fantasy, Thriller, Romance, Adventure, Mystery

- **Movies** (8 movies)
  - The Matrix, Inception, Forrest Gump, The Dark Knight, Interstellar, Pulp Fiction, The Shawshank Redemption, Gladiator

- **TV Shows** (6 shows)
  - Breaking Bad, The Office, Game of Thrones, Stranger Things, The Crown, Westworld

- **Media Requests** (8 requests)
  - Mix of open and completed requests
  - Created by different test users

- **Request Votes**
  - Each user votes on requests they didn't create
  - Demonstrates the voting system

- **Comments**
  - Comments on movies by different users
  - Mix of viewed and unviewed

- **Video Progress**
  - Watch progress for various media items
  - Different users with different watch times

## Usage

### Basic Usage

Load all seed data:

```bash
python manage.py seed_data
```

### Command Options

#### Clear Existing Data

Clear all seed data before creating new data:

```bash
python manage.py seed_data --clear
```

#### Create Users Only

Create only test users, skip all other data:

```bash
python manage.py seed_data --users-only
```

#### Combined Usage

Clear and recreate all data:

```bash
python manage.py seed_data --clear
```

### Example Output

```
Creating seed data...
✓ Created 3 test users
✓ Created 10 genres
✓ Created 8 movies
✓ Created 6 TV shows
✓ Created 8 media requests
✓ Created 14 request votes
✓ Created 14 comments
✓ Created 14 video progress entries

✓ Seed data creation completed successfully!

Test credentials:
  Username: test_user
  Password: password
  Username: demo_user
  Password: password
```

## Testing with Seed Data

### Setup Steps

1. **Clear database and recreate from migrations**
   ```bash
   python manage.py migrate
   ```

2. **Generate seed data**
   ```bash
   python manage.py seed_data
   ```

3. **Start the development servers**

   Terminal 1 - Backend:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

   Terminal 2 - Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Access the application**
   - Navigate to `http://localhost:3000`
   - Login with credentials above

### Testing Scenarios

#### Login & Authentication
- Test login with `test_user` / `password`
- Test admin login with `admin` / `admin`
- Verify token refresh on 401 responses

#### Media Browsing
- Browse movies (8 movies available)
- Browse TV shows (6 shows available)
- Search for specific movies/shows
- View media details
- Test pagination

#### Requests Feature
- View requests page (8 requests)
- Vote on requests created by other users
- See vote counts update in real-time
- Creator can mark their own requests as done
- Test 1-vote-per-day cooldown (try voting twice)

#### Comments Feature
- View comments page (14 comments)
- See mix of viewed/unviewed comments
- Mark comments as viewed
- Delete comments
- Test pagination

#### Video Progress Feature
- View progress page (14 entries)
- See different watch times for different media
- Clear progress entries
- Check progress bars update

#### Collections (if available)
- Create new collections
- Add/remove items from collections
- Delete collections

## Data Structure

### Movies vs TV Shows

- **Movies**: Independent media items
- **TV Shows**: Can have multiple episodes (MediaFile)

Both support:
- Genres
- Comments
- Video progress tracking
- Collections
- Search

### Requests System

- Users can create requests for media
- Other users vote on requests
- Vote cooldown: 1 vote per user per day
- Creators can mark requests as done
- Vote count is displayed

### Comments

- Users can comment on movies
- Comments can be marked as "viewed"
- Each comment tracks when it was created/modified

### Video Progress

- Tracks watched time for each media item
- Stored by hashed filename
- Includes last watch timestamp
- Can be cleared/deleted

## Implementation Details

### File Location
```
mediaviewer/management/commands/seed_data.py
```

### Models Used
- `User` (Django auth)
- `Genre`
- `Movie`
- `TV`
- `Request`
- `RequestVote`
- `Comment`
- `VideoProgress`

### Idempotent Design
The command uses `get_or_create()` for safety:
- Running the command multiple times won't create duplicates
- Safe to run on existing databases
- Use `--clear` to remove and regenerate

## Customization

To add more seed data, edit the following methods in `seed_data.py`:

- `create_movies()` - Add more movies
- `create_tv_shows()` - Add more TV shows
- `create_requests()` - Add more request names
- `create_genres()` - Add more genres

Example adding a movie:
```python
movie_data = [
    {
        "name": "Custom Movie Title",
        "genres": [genres[0], genres[1]],  # Select genre indices
    },
    # ... other movies
]
```

## Troubleshooting

### Command Not Found
```bash
# Make sure you're in the project root
cd /path/to/MediaViewer

# Verify devenv is active
direnv allow
```

### Import Errors
```bash
# Ensure all dependencies are installed
uv pip install -r requirements.txt

# Or use the devenv:
devenv shell
```

### Database Errors
```bash
# Run migrations first
python manage.py migrate

# Then run seed data
python manage.py seed_data --clear
```

## Notes

- The command is designed to be safe and idempotent
- Passwords are hardcoded for testing purposes only
- Do not use in production environments
- Seed data uses realistic but fictional content
- Video progress entries use hashed filenames (no actual files needed)
- Comments are created without linking to actual media files (depends on your schema)

## Future Enhancements

Possible improvements:
- Add command options for custom data quantities
- Generate more realistic data distributions
- Support custom user counts
- Add more complex relationships
- Generate mock media files
- Add performance testing data sets

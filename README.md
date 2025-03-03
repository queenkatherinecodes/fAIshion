# fAIshion - AI-Powered Wardrobe Assistant

## Notes
3/3: To run the app locally this is a pre-requisite:

brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17 mssql-tools

Once you have download sql tools you can run:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## Development Roadmap

### Phase 1: Project Setup
1. Repository Setup
   - [x] Initialize git repository
   - [x] Create README.md
   - [x] Create .gitignore for Python
   - [x] Set up virtual environment
   - [x] Create initial requirements.txt with FastAPI and uvicorn

2. Project Structure
   - [x] Create main application 

3. Database Setup
   - [x] SQL Database with Azure

4. Basic FastAPI Setup
   - [x] Create main FastAPI application instance
   - [x] Set up database connection
   - [x] Add CORS middleware
   - [x] Create health check endpoint
   - [x] Test server runs locally

### Phase 2: DB Setup and Services Scaffolding
5. User Management
   - [ ] Create a table in the SQL database called "Users" with columns: "id", "username", "password"
   - [ ] Create an endpoint "/register" that accepts POST requests with the body { "username" : exampleUser, "password" : ilovebamba123 } and returns 201 Created if an entry to the Users table was successfully added
   - [ ] Create an endpoint "/login" that accepts GET requests with the body { "username" : exampleUser, "password" : ilovebamba123 } and returns 200 OK if that user already exists in the Users table of the database; else return 401 unauthorized
   - [ ] Create Tables for the following clothing items: "Tops", "Bottoms", "Dresses", "Swimsuits", "Shoes", "Accessories", "Miscellaneous" and decide on a scheme for each of them. All should have a unique identifier and include the "userId" from the Users table as a column. 
   - [ ] Create an endpoint "/api/clothing" that accepts POST requests with body { "userId": $someUserId, "description": "little black dress" } and implement the logic that enters it into its appropriate table
   - [ ] RESEARCH: how to upload an image in a request similar to the POST request for "/api/clothing" so that we can use images in addition to text descriptions

6. Services Scaffolding
   - [ ] Create a directory "src/app/services" and add the files weather_service.py, open_ai_service.py, etc. (need to brainstorm what we will be accessing)
   - [ ] Equipt each service with the necessary API tokens, python packages, etc. so that methods containing logic can easily be added without any set up
   - [ ] RESEARCH: come up with the WOW factor AI model feature that's more than just a GPT wrapper that is going to be the va va voom of our project



# EVERYTHING BELOW HERE IS JUST AN AI GENERATED SUGGESTION....
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
### Phase 3: Core Wardrobe Features
6. Wardrobe Item Management
   - [ ] Create WardrobeItem schema
   - [ ] Add endpoint to create item (POST /api/wardrobe)
   - [ ] Add endpoint to list items (GET /api/wardrobe)
   - [ ] Add endpoint to get single item (GET /api/wardrobe/{id})
   - [ ] Add endpoint to update item (PUT /api/wardrobe/{id})
   - [ ] Add endpoint to delete item (DELETE /api/wardrobe/{id})
   - [ ] Add basic input validation
   - [ ] Add user-wardrobe relationship

7. Image Handling
   - [ ] Research and choose computer vision API
   - [ ] Set up cloud storage (AWS S3 bucket)
   - [ ] Create image upload endpoint
   - [ ] Add image validation
   - [ ] Create image processing service
   - [ ] Implement automatic clothing type detection
   - [ ] Add color detection
   - [ ] Store image metadata

### Phase 4: AI Integration
8. OpenAI Integration
   - [ ] Set up OpenAI API client
   - [ ] Create environment variables for API keys
   - [ ] Create prompt engineering service
   - [ ] Add rate limiting for API calls
   - [ ] Add error handling for API calls

9. Outfit Recommendation
   - [ ] Create recommendation endpoint (POST /api/outfits/recommend)
   - [ ] Implement basic matching algorithm
   - [ ] Add filters (weather, occasion, etc.)
   - [ ] Create outfit history tracking
   - [ ] Add feedback mechanism

### Phase 5: Testing
10. Unit Tests
    - [ ] Set up pytest
    - [ ] Add test database configuration
    - [ ] Write tests for user authentication
    - [ ] Write tests for wardrobe operations
    - [ ] Write tests for AI recommendations

11. Integration Tests
    - [ ] Add API tests
    - [ ] Test image upload flow
    - [ ] Test recommendation flow
    - [ ] Add test coverage reporting

### Phase 6: Documentation and Cleanup
12. API Documentation
    - [ ] Add docstrings to all functions
    - [ ] Set up Swagger UI
    - [ ] Document all endpoints
    - [ ] Add usage examples

13. Code Quality
    - [ ] Add type hints
    - [ ] Set up black for formatting
    - [ ] Set up flake8 for linting
    - [ ] Add pre-commit hooks

### Phase 7: Deployment Prep
14. Deployment Setup
    - [ ] Create Dockerfile
    - [ ] Add docker-compose for local development
    - [ ] Create production configuration
    - [ ] Add logging configuration
    - [ ] Create deployment documentation

Each task should be completed and tested before moving on to the next one. The phases can be worked on in parallel by different team members if needed.
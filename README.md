# Travel Planner API (Junior Test Assessment)

This is a RESTful API for a Travel Planning system built with FastAPI and SQLAlchemy.

### Features:
- **Project Management**: Create, list, and delete travel projects.
- **Location Integration**: Add places to projects using the Art Institute of Chicago API.
- **Business Logic**: 
  - Maximum 10 places per project.
  - Prevent duplicate places in the same project.
  - Cannot delete a project if any of its places are marked as "visited".
- **Data Persistence**: Uses SQLite to store data.

### How to Run:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
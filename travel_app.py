from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "sqlite:///./travel_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ProjectDB(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    places_json = Column(Text, default="[]") 

Base.metadata.create_all(bind=engine)

app = FastAPI()

class PlaceCreate(BaseModel):
    location_id: str
    notes: Optional[str] = ""

@app.post("/projects/")
def create_project(name: str, description: str = None):
    db = SessionLocal()
    new_project = ProjectDB(name=name, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    db.close()
    return new_project

@app.post("/projects/{project_id}/places/")
async def add_place(project_id: int, place: PlaceCreate):
    db = SessionLocal()
    project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
    
    if not project:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found") 

    current_places = json.loads(project.places_json)

 
    if len(current_places) >= 10:
        db.close()
        raise HTTPException(status_code=400, detail="Maximum 10 places allowed")

    
    if any(p["location_id"] == place.location_id for p in current_places):
        db.close()
        raise HTTPException(status_code=400, detail="Place already exists in this project")

    
    url = f"https://api.artic.edu/api/v1/artworks/{place.location_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            db.close()
            raise HTTPException(status_code=400, detail="Place not found in Chicago Art Institute")
        
        api_data = resp.json()
        title = api_data["data"]["title"]

    new_place_data = {
        "location_id": place.location_id,
        "title": title,
        "notes": place.notes,
        "visited": False
    }
    
    current_places.append(new_place_data)
    project.places_json = json.dumps(current_places)
    db.commit()
    db.close()
    return {"status": "success", "added": title}

@app.delete("/projects/{project_id}")
def delete_project(project_id: int):
    db = SessionLocal()
    project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
    
    if not project:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    
    places = json.loads(project.places_json)

    
    if any(p.get("visited") is True for p in places):
        db.close()
        raise HTTPException(status_code=400, detail="Cannot delete project with visited places")
    
    db.delete(project)
    db.commit()
    db.close()
    return {"message": "Project deleted"}

@app.get("/projects/")
def get_projects():
    db = SessionLocal()
    projects = db.query(ProjectDB).all()
    
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "places": json.loads(p.places_json)
        })
    db.close()
    return result
@app.patch("/projects/{project_id}/places/{location_id}/visit")
def mark_as_visited(project_id: int, location_id: str):
    db = SessionLocal()
    project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
    if not project:
        db.close()
        raise HTTPException(status_code=404, detail="Project not found")
    
    places = json.loads(project.places_json)
    found = False
    for p in places:
        if p["location_id"] == location_id:
            p["visited"] = True
            found = True
            break
    
    if not found:
        db.close()
        raise HTTPException(status_code=404, detail="Place not found in project")
        
    project.places_json = json.dumps(places)
    db.commit()
    db.close()
    return {"message": "Status updated to visited"}
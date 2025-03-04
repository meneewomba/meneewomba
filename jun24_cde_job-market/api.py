from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import get_db  # Import new database function

app = FastAPI()

class SearchPayload(BaseModel):
    must_contain: Optional[List[str]] = None
    contain_any: Optional[List[str]] = None
    not_contain: Optional[List[str]] = None
    

@app.post("/search/")
def search_jobs(payload: SearchPayload, db=Depends(get_db)):
    where_conditions = []
    params = []
    
    # Handle `contain_any` condition (using AND)
    if payload.must_contain:
        contain_conditions = " AND ".join([f"description LIKE %s" for _ in payload.must_contain])
        where_conditions.append(f"({contain_conditions})")
        params.extend([f"%{word}%" for word in payload.must_contain])  # Add parameters

    # Handle `contain_any` condition (using OR)
    if payload.contain_any:
        contain_any_conditions = " OR ".join([f"description LIKE %s" for _ in payload.contain_any])
        where_conditions.append(f"({contain_any_conditions})")
        params.extend([f"%{word}%" for word in payload.contain_any])  # Add parameters

    

    # Handle `not_contain` condition (using OR inside parentheses)
    if payload.not_contain:
        not_conditions = " OR ".join([f"description NOT LIKE %s" for _ in payload.not_contain])
        where_conditions.append(f"({not_conditions})")
        params.extend([f"%{word}%" for word in payload.not_contain])  # Add parameters

    # Combine all conditions with AND
    if where_conditions:
        query = "SELECT a.title, CONCAT('https://candidat.francetravail.fr/offres/recherche/detail/', a.internal_id) as link, b.label as contract_type, case when c.max_monthly_salary is null then CONCAT('à partir de ', c.min_monthly_salary) else CONCAT('de ', c.min_monthly_salary, ' à ', c.max_monthly_salary) end as salary, d.name as city FROM job a join job_contract b on a.job_id = b.job_id join salary c on a.job_id = c.job_id join cities d on a.insee_code = d.insee_code   WHERE " + " AND ".join(where_conditions)
    else:
        query = "SELECT a.title, CONCAT('https://candidat.francetravail.fr/offres/recherche/detail/', a.internal_id) as link, b.label as contract_type, case when c.max_monthly_salary is null then CONCAT('à partir de ', c.min_monthly_salary) else CONCAT('de ', c.min_monthly_salary, ' à ', c.max_monthly_salary) end as salary,  d.name as city FROM job a join job_contract b on a.job_id = b.job_id join salary c on a.job_id = c.job_id join cities d on a.insee_code = d.insee_code" # No where conditions
    try:
        with get_db() as cursor:  # This ensures cursor is automatically closed
            if cursor is None:
                raise HTTPException(status_code=500, detail="Database connection error")
            cursor.execute(query, params)  # Synchronously executing query
            result = cursor.fetchall()  # Synchronously fetch results
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

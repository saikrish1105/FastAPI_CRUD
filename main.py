from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated,Literal,Optional
import json 

app = FastAPI()

# Pydantic Models for verification
class Patient(BaseModel):
    # Annotated is used to describe the fields with additional metadata
    id : Annotated[str, Field(...,description="The unique identifier for the patient", examples=["P001"])]
    name : Annotated[str, Field(...,description="The name of the patient")]
    city : Annotated[str, Field(...,description="The city where the patient resides")]
    age : Annotated[int, Field(...,gt=0,lt=120,description="The age of the patient")]
    gender : Annotated[Literal['male','female','others'], Field(...,description="The gender of the patient")]
    height : Annotated[float, Field(...,gt=0.0,description="The height of the patient in mtrs")]
    weight : Annotated[float, Field(...,gt=0.0,description="The weight of the patient in kg")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"

class PatientUpdate(BaseModel):
    name : Annotated[Optional[str], Field(default=None)]
    city : Annotated[Optional[str], Field(default=None)]
    age : Annotated[Optional[int], Field(default=None, gt=0)]
    gender : Annotated[Optional[Literal['male','female','others']], Field(default=None)]
    height : Annotated[Optional[float], Field(default=None, gt=0)]
    weight : Annotated[Optional[float], Field(default=None, gt=0)]

# Basic Site Information Endpoints
@app.get("/")
def start():
    return {"message": "Patient Management System"}

@app.get("/about")
def about():
    return {"information": "This is a Patient Management System built with FastAPI"}


# Create Patient Data Endpoint
@app.post('/create')
def create_patient(patient: Patient):
    #load existing data
    data = load_data()

    #check if patient exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient Already Exists")
    
    #add new data
    data[patient.id] = patient.model_dump(exclude=['id'])

    #save into json file
    save_data(data)
    
    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient_id": patient.id})

# Update Patient Data Endpoint
@app.put("/update/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):

    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=400,detail="Patient Does Not Exists")

    existing_patient_info = data[patient_id] 
    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    # updating key value from updated into existing 
    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    # convert existing patient info to Pydantic model to calculate bmi and verdict
    existing_patient_info['id'] = patient_id
    patient_pydantic = Patient(**existing_patient_info)

    # convert back to dict
    existing_patient_info = patient_pydantic.model_dump(exclude=['id'])

    # add dict to data
    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code=201, content={"message": "Patient updated Succesfuly", "patient_id": patient_id})

# Delete Patient Data Endpoint
@app.delete("/delete/{patient_id}")
def delete(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=400, detail="Patient Does Not Exists")

    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully", "patient_id": patient_id})

# Retrieve Endpoints
@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/patient/{patient_id}")
def get_patient(patient_id : str = Path(...,description="The ID of the patient to retrieve", example="P001")):
    data = load_data()
    if patient_id in data: 
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by: str = Query(...,description="Sort on the basis of height, weight,age or bmi"), order: str=Query('asc',description="Order of sorting")):
    valid_sort_fields = ['height', 'weight', 'bmi', 'age']
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field. Choose from {valid_sort_fields}.")

    if order not in ['asc', 'dsc']:
        raise HTTPException(status_code=400, detail="Invalid order. Choose 'asc' or 'dsc'.")
    
    data = load_data()

    sort_order = True if order == 'dsc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by,0), reverse=sort_order)

    return sorted_data


# Functions for data manipulation
def load_data():
    with open("patients.json", "r") as file:
        data = json.load(file)
    return data

def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f)

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from backend.utils import util
from backend.utils.db_session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel


router = APIRouter()


# Request Models
class SignUpRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    height: int
    weight: int
    age: int
    gender: str
    activity_level: str
    target: str
    preference: str


class DietHistoryRequest(BaseModel):
    calories: int
    protein: int
    carbohydrates: int
    fat: int


@router.post("/signup")
async def sign_up(signup_request: SignUpRequest, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = util.get_user_by_username(signup_request.username, db)
    if existing_user:
        return {"error": "Username already taken"}

    # Hash the password (this function should be defined in `util.py`)
    hashed_password = util.hash_password(signup_request.password)

    # Save the new user in the database
    new_user = util.create_user(
        username=signup_request.username,
        password=hashed_password,
        db=db
    )

    # Create JWT token
    token = util.create_access_token(data={"sub": signup_request.username})

    return {"jwtToken": token, "message": f"User {signup_request.username} Login successful"}


@router.post("/login")
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    # Authenticate user using the single database
    auth_result = util.authenticate_user(login_request.username, login_request.password, db)

    if "error" in auth_result:
        return {"error": auth_result["error"]}  # Return specific error message

    user_name = auth_result["user"]

    # Create JWT token
    token = util.create_access_token(data={"sub": login_request.username})

    # Return the token in the response body
    return {"jwtToken": token, "message": f"User {user_name} Login successful"}


@router.get("/get_user_info")
async def get_user_info(db: Session = Depends(get_db), username: str = Depends(util.get_current_user)):
    user_info = util.get_user_info(username, db)

    if user_info:
        return {
            "height": user_info.height,
            "weight": user_info.weight,
            "age": user_info.age,
            "gender": user_info.gender,
            "activity_level": user_info.activity_level,
            "target": user_info.target,
            "preference": user_info.preference,
            'tdee': user_info.tdee,
            'target_protein': user_info.target_protein,
            'target_carbohydrates': user_info.target_carbohydrates,
            'target_fat': user_info.target_fat
        }
    return {"error": "User info not found"}


@router.post("/save_user_info")
async def save_user_info(user_info: UserInfo, db: Session = Depends(get_db), username: str = Depends(util.get_current_user)):
    # Save user info to the database for the current user
    result = util.save_user_info_to_db(user_info, db, username)

    if result:
        return {"message": "User info saved successfully"}
    return {"error": "Failed to save user info"}


@router.post("/analyze")
async def analyze(
    food_img: UploadFile = File(None),  # Make food_img optional
    db: Session = Depends(get_db),
    user_name: str = Depends(util.get_current_user),
    manual_protein: int = Form(None),  # Make manual input fields optional
    manual_carbohydrates: int = Form(None),
    manual_fat: int = Form(None),
    time_zone: str = Form(...),  # Time zone should be mandatory
):
    # Ensure that at least one data source (image or manual input) is provided
    if not food_img and not (manual_protein and manual_carbohydrates and manual_fat):
        raise HTTPException(status_code=422, detail="You must provide either an image or manual nutrient values.")

    obj = {}

    # If an image is provided, read it
    if food_img:
        image_bytes = await food_img.read()
        obj['img'] = image_bytes

    # If manual input is provided, include it in the obj
    if manual_protein and manual_carbohydrates and manual_fat:
        obj['protein'] = manual_protein
        obj['carbohydrates'] = manual_carbohydrates
        obj['fat'] = manual_fat

    analysis_result = util.analysis(obj, db, user_name=user_name, time_zone=time_zone)
    return {"result": analysis_result}


@router.post("/save_diet_history")
async def save_diet_history(
    food_img: UploadFile = File(None),
    calories: int = Form(...),
    protein: int = Form(...),
    carbohydrates: int = Form(...),
    fat: int = Form(...),
    db: Session = Depends(get_db),
    username: str = Depends(util.get_current_user)
):

    # If an image is provided, read it
    if food_img:
        image_bytes = await food_img.read()
    else:
        image_bytes = None

    saved_history = util.save_diet_history(
        user=username,
        meal='lunch',
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fat=fat,
        image_bytes=image_bytes,
        db=db,
    )

    if saved_history:
        return {"message": "Diet history saved successfully"}
    else:
        return {"error": "Failed to save diet history"}


@router.get("/get_diet_history")
async def get_diet_history(db: Session = Depends(get_db), username: str = Depends(util.get_current_user)):
    # Fetch the diet history from the database using the `get_diet_history` utility function
    diet_history = util.get_diet_history_from_db(username, db)
    if not diet_history:
        return {"error": "No diet history found for this user"}

    # Return the diet history in a structured format
    return {"diet_history": diet_history}
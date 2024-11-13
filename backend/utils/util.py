from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.models.database import User, Diet, Food, Workout
from backend.utils.db_session import get_db
from backend.utils.openai_api import img_analysis
from backend.utils.s3_api import upload_file_to_s3
import os
import uuid
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# OAuth2PasswordBearer for extracting the token from the header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_user_by_username(username: str, db: Session):
    return db.query(User).filter(User.user == username).first()


def hash_password(password: str):
    return pwd_context.hash(password)


def create_user(username: str, password: str, db: Session):
    new_user = User(
        user=username,
        password=password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 1. Authenticate User (Interacts with User Info DB)
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.user == username).first()

    if not user:
        return {"error": "User not found"}  # Specific case for user not found
    if not verify_password(password, user.password):
        return {"error": "Incorrect password"}  # Specific case for wrong password
    return {"user": user}  # Return user data if both username and password are correct


# Password verification
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


# 2. Create Access Token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 3. Save User Info (Interacts with User Info DB)
def save_user_info_to_db(user_info, db: Session, username: str):
    # Find the user by the username from the JWT token
    existing_user = db.query(User).filter(User.user == username).first()

    if not existing_user:
        return None  # Handle user not found error

    # Update the user's profile with the provided data
    existing_user.height = user_info.height
    existing_user.weight = user_info.weight
    existing_user.age = user_info.age
    existing_user.gender = user_info.gender
    existing_user.activity_level = user_info.activity_level
    existing_user.target = user_info.target
    existing_user.preference = user_info.preference

    target = get_target_number(user_info)

    existing_user.tdee = target['calories']
    existing_user.target_protein = target['protein']
    existing_user.target_carbohydrates = target['carbohydrates']
    existing_user.target_fat = target['fat']

    # Commit the changes to the database
    db.commit()
    db.refresh(existing_user)  # Refresh the instance with the latest data

    return existing_user  # Optionally return the updated user


def verify_jwt_token(token: str):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # Extract the username from the token payload

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username  # Return the username for further use

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Step 1: Verify the token and get the username
    username = verify_jwt_token(token)

    # Step 2: Extract the user from the database
    user = db.query(User).filter(User.user == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user.user  # Return the user object


def get_user_info(username: str, db: Session):
    # Query the database to get the user information by username
    user_info = db.query(User).filter(User.user == username).first()

    if user_info:
        return user_info  # Return the user information object

    return None  # Return None if no user is found


# get today diet history
def get_intake_sum_today(user: str, db: Session, time_zone: str):
    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Convert UTC time to the client's timezone
    client_tz = pytz.timezone(time_zone)
    client_now = utc_now.astimezone(client_tz)

    # Get the start and end of the day in the client's timezone
    client_start_of_day = client_tz.localize(datetime(client_now.year, client_now.month, client_now.day, 0, 0, 0))
    client_end_of_day = client_start_of_day + timedelta(days=1)

    # Convert start and end of day to UTC for the query
    utc_start_of_day = client_start_of_day.astimezone(pytz.UTC)
    utc_end_of_day = client_end_of_day.astimezone(pytz.UTC)

    # Query the database to sum up calories, protein, carbohydrates, and fat
    totals = db.query(
        func.sum(Diet.calories).label('total_calories'),
        func.sum(Diet.protein).label('total_protein'),
        func.sum(Diet.carbohydrates).label('total_carbohydrates'),
        func.sum(Diet.fat).label('total_fat')
    ).filter(
        Diet.user == user,
        Diet.datetime >= utc_start_of_day,
        Diet.datetime < utc_end_of_day
    ).first()

    # Return the summed totals in the desired format
    result = {
        "calories": int(totals.total_calories or 0),  # Cast to int, handle None by defaulting to 0
        "protein": int(totals.total_protein or 0),
        "carbohydrates": int(totals.total_carbohydrates or 0),
        "fat": int(totals.total_fat or 0)
    }

    return result


def get_target_number(user_info):
    # Calculate TDEE based on height, weight, age, gender, and activity level
    def calculate_tdee(height, weight, age, gender, activity_level):
        if gender == 'Male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        elif gender == 'Female':
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        else:
            raise ValueError("Gender must be 'male' or 'female'")

        # TDEE is BMR multiplied by the activity factor
        activity_factors = {
            'Sedentary': 1.2,
            'Lightly Active': 1.375,
            'Moderately Active': 1.55,
            'Very Active': 1.725
        }

        return bmr * activity_factors.get(activity_level, 1.2)  # Default to sedentary if not provided

    # Suggest macronutrient intake based on the user's goal and preference
    def suggest_macronutrients(tdee, target, preference):
        if target == 'Gain Muscle':
            protein_ratio = 0.3 if preference == 'High Protein' else 0.25
            carb_ratio = 0.4 if preference == 'Balanced' else 0.3
            fat_ratio = 0.3 if preference == 'Balanced' else 0.4
        elif target == 'Lose Weight':
            protein_ratio = 0.25 if preference == 'High Protein' else 0.2
            carb_ratio = 0.35 if preference == 'Low Carb' else 0.45
            fat_ratio = 0.4 if preference == 'Low Carb' else 0.35
        else:  # Maintain Fitness
            protein_ratio = 0.25
            carb_ratio = 0.5 if preference == 'Balanced' else 0.45
            fat_ratio = 0.25 if preference == 'Balanced' else 0.3

        # Calculate grams of each macronutrient (1g protein/carbs = 4 kcal, 1g fat = 9 kcal)
        protein = (protein_ratio * tdee) / 4
        carbohydrates = (carb_ratio * tdee) / 4
        fat = (fat_ratio * tdee) / 9

        return {
            'protein': round(protein),
            'carbohydrates': round(carbohydrates),
            'fat': round(fat)
        }

    # Use the user's height, weight, age, gender, and activity level
    tdee = calculate_tdee(user_info.height, user_info.weight, user_info.age, user_info.gender, user_info.activity_level)

    # Get target values for macronutrients based on the user's goal and dietary preference
    macronutrient_targets = suggest_macronutrients(tdee, user_info.target, user_info.preference)

    # Return the calculated values (TDEE and macronutrient targets)
    return {
        'calories': round(tdee),
        **macronutrient_targets
    }


# 6. Analyze Function (Interacts with All 4 Databases)
def analysis(obj, db: Session, user_name: str, time_zone: str):
    user_info = get_user_info(user_name, db)
    intake_target = {
        'calories': user_info.tdee,
        'protein': user_info.target_protein,
        'carbohydrates': user_info.target_carbohydrates,
        'fat': user_info.target_fat
    }

    intake_prior = get_intake_sum_today(user_name, db, time_zone)

    if 'protein' not in obj:
        intake_current = img_analysis(image_bytes=obj['img'])
        # intake_current = {'protein': 25, 'carbohydrates': 30, 'fat': 15, 'calories': 355}
    else:
        if 'img' in obj:
            del obj['img']
        intake_current = obj
    # meal_ingredient = {'pork': 100, 'egg': 50, 'vegetables': 200, 'milk': 30}

    intake_current['calories'] = intake_current['protein']*4 + intake_current['carbohydrates']*4 + intake_current['fat']*9
    print(intake_current)

    result = {
        'intake_current': intake_current,
        'intake_prior': intake_prior,
        'intake_target': intake_target
    }

    return result


# 5 Save Diet History into the Database
def save_diet_history(user: str, meal: str, calories: int, protein: int, carbohydrates: int, fat: int
                      ,db: Session, image_bytes: bytes = None):

    if image_bytes:
        unique_id = str(uuid.uuid4())
        hash_object = hashlib.sha256(image_bytes[:1024])
        hash_prefix = hash_object.hexdigest()[:8]
        filename = f"{unique_id}_{hash_prefix}"
        img_url = upload_file_to_s3(filename, image_bytes)
    # img_url = 'https://via.placeholder.com/150'
    else:
        img_url = None

    # Create a new Diet history entry
    new_diet_entry = Diet(
        user=user,
        meal=meal,
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fat=fat,
        img_url=img_url,
        datetime=datetime.utcnow()
    )

    # Add the new entry to the session and commit it to the database
    db.add(new_diet_entry)
    db.commit()
    db.refresh(new_diet_entry)  # Refresh to get the latest state of the new entry (e.g., auto-generated ID)

    return new_diet_entry, img_url  # Optionally return the newly created entry


def get_diet_history_from_db(username: str, db: Session, filter_date: datetime.date = None):
    # Define the Taipei timezone
    taipei_tz = pytz.timezone('Asia/Taipei')

    # Convert the input filter_date from Taipei time to UTC time if a filter is provided
    if filter_date:
        # Assuming the filter_date is a date object (YYYY-MM-DD) without time
        start_of_day_taipei = taipei_tz.localize(datetime.combine(filter_date, datetime.min.time()))
        end_of_day_taipei = taipei_tz.localize(datetime.combine(filter_date, datetime.max.time()))

        # Convert start and end of the day from Taipei time to UTC
        start_of_day_utc = start_of_day_taipei.astimezone(pytz.utc)
        end_of_day_utc = end_of_day_taipei.astimezone(pytz.utc)

        # Filter the entries between start and end of the day in UTC
        history = db.query(Diet).filter(Diet.user == username,
                                        Diet.datetime >= start_of_day_utc,
                                        Diet.datetime <= end_of_day_utc).order_by(Diet.datetime.desc()).all()
    else:
        # If no filter date is provided, fetch all entries
        history = db.query(Diet).filter(Diet.user == username).order_by(Diet.datetime.desc()).all()

    # Structure the response in the desired format
    result = []
    for entry in history:
        result.append({
            "datetime": entry.datetime,
            "meal": entry.meal,
            "calories": entry.calories,
            "protein": entry.protein,
            "carbohydrates": entry.carbohydrates,
            "fat": entry.fat,
            'img_url': entry.img_url
        })

    return result


def analysis_gemini(food_recognition):
    """Return the complete formatted output matching the required format"""
    food_items = food_recognition.get_food_list_with_nutrition()
    food_labels = [item["label"] for item in food_items]
    bounding_boxes = food_recognition.get_bounding_boxes(food_labels)
    
    formatted_list = []
    
    for idx, food_item in enumerate(food_items):
        formatted_item = {
            "label": food_item["label"],
            "bbox": bounding_boxes[food_item["label"]],
            "nutrition": food_item["nutrition"]
        }
        formatted_list.append(formatted_item)

    return {
        "pixel": list(food_recognition.pixel),
        "list": formatted_list
    }

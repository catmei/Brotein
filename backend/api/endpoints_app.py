from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from backend.utils import util
from backend.utils.db_session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Optional
import shutil
import os
from backend.utils.gemini_api import FoodRecognition

router = APIRouter()


# Request Models
class SignUpRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfoResponse(BaseModel):
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


class BaseResponse(BaseModel):
    message: str
    data: Optional[Any] = None


class SignupResponseData(BaseModel):
    jwtToken: str


class LoginResponseData(BaseModel):
    jwtToken: str


def create_success_response(message: str, data: Optional[Any] = None) -> BaseResponse:
    return BaseResponse(message=message, data=data)


def create_error_response(code: int, details: str) -> HTTPException:
    return HTTPException(
        status_code=code,
        detail=details
    )


@router.post("/signup", response_model=BaseResponse, responses={
    200: {
        "description": "Signup Successful",
        "content": {
            "application/json": {
                "example": {
                    "message": "User XXX signup successful",
                    "data": {"jwtToken": "example.jwt.token"}
                }
            }
        }
    },
    400: {
        "description": "Bad Request - Username already used",
        "content": {
            "application/json": {
                "example": {
                    "details": "The username is already in use. Please choose a different username"
                }
            }
        }
    }
})
async def sign_up(signup_request: SignUpRequest, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = util.get_user_by_username(signup_request.username, db)
    if existing_user:
        raise create_error_response(
            code=status.HTTP_400_BAD_REQUEST,
            details="The username is already in use. Please choose a different username"
        )

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

    return create_success_response(
        message=f"User {signup_request.username} signup successful",
        data=SignupResponseData(jwtToken=token)
    )


@router.post("/login", response_model=BaseResponse, responses={
    200: {
        "description": "Login Successful",
        "content": {
            "application/json": {
                "example": {
                    "message": "User XXX login successful",
                    "data": {"jwtToken": "example.jwt.token"}
                }
            }
        }
    },
    400: {
        "description": "Bad Request - Invalid credential",
        "content": {
            "application/json": {
                "example": {
                    "details": "User not found / Incorrect password"
                }
            }
        }
    }
})
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    # Authenticate user using the single database
    auth_result = util.authenticate_user(login_request.username, login_request.password, db)

    if "error" in auth_result:
        raise create_error_response(
            code=status.HTTP_400_BAD_REQUEST,
            details=auth_result["error"]
        )

    user_name = auth_result["user"]

    # Create JWT token
    token = util.create_access_token(data={"sub": login_request.username})

    return create_success_response(
        message=f"User {user_name} login successful",
        data=LoginResponseData(jwtToken=token)
    )


@router.get("/get_user_info", response_model=BaseResponse, responses={
    200: {
        "description": "User Info Retrieved Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "User info retrieved successfully",
                    "data": {
                        "height": 180,
                        "weight": 75,
                        "age": 29,
                        "gender": "male",
                        "activity_level": "moderate",
                        "target": "gain muscle",
                        "preference": "high protein",
                        "tdee": 2500,
                        "target_protein": 150,
                        "target_carbohydrates": 300,
                        "target_fat": 80
                    }
                }
            }
        }
    },
    404: {
        "description": "User Info Not Found",
        "content": {
            "application/json": {
                "example": {
                    "details": "User XXX information not found"
                }
            }
        }
    }
})
async def get_user_info(db: Session = Depends(get_db), username: str = Depends(util.get_current_user)):
    user_info = util.get_user_info(username, db)

    if not user_info:
        raise create_error_response(
            code=status.HTTP_404_NOT_FOUND,
            details=f"User {username} information not found"
        )

    return create_success_response(
        message="User info retrieved successfully",
        data=UserInfoResponse(
            height=user_info.height,
            weight=user_info.weight,
            age=user_info.age,
            gender=user_info.gender,
            activity_level=user_info.activity_level,
            target=user_info.target,
            preference=user_info.preference,
            tdee=user_info.tdee,
            target_protein=user_info.target_protein,
            target_carbohydrates=user_info.target_carbohydrates,
            target_fat=user_info.target_fat
        )
    )


@router.post("/save_user_info", response_model=BaseResponse, responses={
    200: {
        "description": "User Info Saved Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "User info saved successfully"
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Failed to Save User Info",
        "content": {
            "application/json": {
                "example": {
                    "details": "An error occurred while saving the user info"
                }
            }
        }
    }
})
async def save_user_info(user_info: UserInfoResponse, db: Session = Depends(get_db),
                         username: str = Depends(util.get_current_user)):
    # Save user info to the database for the current user
    result = util.save_user_info_to_db(user_info, db, username)

    if not result:
        raise create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details="An error occurred while saving the user info"
        )

    return create_success_response(
        message="User info saved successfully"
    )


@router.post("/analyze", response_model=BaseResponse, responses={
    200: {
        "description": "Analysis Completed Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Analysis completed successfully",
                    "data": {
                        "result": {
                            "protein": 25,
                            "carbohydrates": 45,
                            "fat": 15
                        }
                    }
                }
            }
        }
    },
    422: {
        "description": "Unprocessable Entity - Missing Required Data",
        "content": {
            "application/json": {
                "example": {
                    "details": "You must provide either an image or manual nutrient values"
                }
            }
        }
    }
})
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
        raise create_error_response(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details="You must provide either an image or manual nutrient values"
        )

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
    return create_success_response(
        message="Analysis completed successfully",
        data={"result": analysis_result}
    )


@router.post("/save_diet_history", response_model=BaseResponse, responses={
    200: {
        "description": "Diet History Saved Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Diet history saved successfully"
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - Failed to Save Diet History",
        "content": {
            "application/json": {
                "example": {
                    "details": "An error occurred while saving the diet history"
                }
            }
        }
    }
})
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

    if not saved_history:
        raise create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details="An error occurred while saving the diet history"
        )
    return create_success_response(message="Diet history saved successfully")


@router.get("/get_diet_history", response_model=BaseResponse, responses={
    200: {
        "description": "Diet History Retrieved Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Diet history retrieved successfully",
                    "data": {
                        "diet_history": [
                            {
                                "date": "2024-10-29",
                                "meal": "lunch",
                                "calories": 500,
                                "protein": 30,
                                "carbohydrates": 50,
                                "fat": 20
                            },
                            {
                                "date": "2024-10-28",
                                "meal": "dinner",
                                "calories": 600,
                                "protein": 40,
                                "carbohydrates": 60,
                                "fat": 25
                            }
                        ]
                    }
                }
            }
        }
    }
})
async def get_diet_history(db: Session = Depends(get_db), username: str = Depends(util.get_current_user)):
    # Fetch the diet history from the database using the `get_diet_history` utility function
    diet_history = util.get_diet_history_from_db(username, db)

    # Return the diet history in a structured format
    return create_success_response(
        message="Diet history retrieved successfully",
        data={"diet_history": diet_history}
    )


@router.post("/analyze_gemini", response_model=BaseResponse, responses={
    200: {
        "description": "Gemini Analysis Completed Successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Gemini analysis completed successfully",
                    "data": {
                        "pixel": [600, 800],
                        "list": [
                            {
                                "label": "food1",
                                "bbox": [882, 795, 1000, 812],
                                "nutrition": {
                                    "Calories": 100,
                                    "Fat": 10,
                                    "Protein": 20,
                                    "Carbs": 30
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
})
async def analyze_gemini(food_img: UploadFile = File(...)):
    if not food_img:
        raise create_error_response(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details="You must provide an image file"
        )

    try:
        # Read image bytes directly
        image_bytes = await food_img.read()
        
        # Create an instance of FoodRecognition with bytes
        food_recognition = FoodRecognition(image_bytes)
        formatted_output = util.analysis_gemini(food_recognition)

        return create_success_response(
            message="Gemini analysis completed successfully",
            data=formatted_output
        )
    finally:
        await food_img.close()
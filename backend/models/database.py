from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

# Base model
Base = declarative_base()


# User Model (with relationship to Diet)
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user = Column(String(45), unique=True, index=True)
    password = Column(String(255))
    gender = Column(String(45))
    height = Column(Integer)
    weight = Column(Integer)
    age = Column(Integer)
    activity_level = Column(String(45))
    target = Column(String(45))
    preference = Column(String(45))
    tdee = Column(Integer)
    target_protein = Column(Integer)
    target_carbohydrates = Column(Integer)
    target_fat = Column(Integer)


# Diet Model (equivalent to diet_history table, with ForeignKey to User)
class Diet(Base):
    __tablename__ = "diet_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user = Column(String(45))
    meal = Column(String(45))  # Meal type (breakfast, lunch, etc.)
    calories = Column(Integer)
    protein = Column(Integer)
    carbohydrates = Column(Integer)
    fat = Column(Integer)
    datetime = Column(DateTime)
    img_url = Column(String(255))


# Food Model (independent)
class Food(Base):
    __tablename__ = "food_nutrition"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    food = Column(String(45))  # Food name
    calories = Column(Integer)
    protein = Column(Integer)
    carbohydrates = Column(Integer)
    fat = Column(Integer)


# Workout Model (independent)
class Workout(Base):
    __tablename__ = "workout"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(45))  # Workout name
    calories_consumption = Column(Integer)  # Calories burned
    type = Column(String(45))  # Workout type (cardio, strength, etc.)

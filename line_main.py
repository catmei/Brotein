from fastapi import FastAPI, Request
import uvicorn
import json
from line_utils import *
from backend.utils.openai_api import img_analysis
from backend.utils.util import save_diet_history, get_diet_history_from_db
from backend.utils.db_session import get_db
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# LINE Messaging API endpoint and channel access token
LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CONTENT_ENDPOINT = "https://api-data.line.me/v2/bot/message/{message_id}/content"


app = FastAPI()
nutrition_cache = {}
history_cache = {}


@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()

    print(f'datetime: {datetime.now()}')
    print(json.dumps(body, indent=4))

    # Check if it's a message or postback event
    if "events" in body and len(body["events"]) > 0:
        event = body["events"][0]
        user_id = event['source']['userId']
        reply_token = event["replyToken"]

        # Check if the event is 'follow' (user added the bot) or 'join' (bot joined a group)
        # if event["type"] == "follow" or event["type"] == "join":
        #     reply_message = "Hello"
        #     reply_status = await reply_with_message(reply_token, reply_message)
        #     print(f"Welcome message sent: {reply_status}")
        #     return {"status": "ok"}

        # Handle postback action
        if event["type"] == "postback":
            postback_data = event["postback"]["data"]

            # If the postback data is for cancel, do nothing
            if postback_data == "action=cancel":
                print("User canceled the action.")
                return {"status": "ok"}

            # Check if the postback data is for triggering the camera
            if postback_data == "action=trigger_camera":
                # Send Quick Reply with camera action
                reply_status = await reply_with_camera_quick_reply(reply_token)
                print(f"Quick Reply with camera sent: {reply_status}")
                return {"status": "ok"}

            # Check if the postback is for saving the data
            if postback_data == "action=save":
                await start_loading_animation(chat_id=user_id)
                if user_id in nutrition_cache:
                    # Save the data from cache using the save_diet_history function
                    user = nutrition_cache[user_id]
                    rotated_img = rotate_image_if_vertical(user['image'])
                    saved_history = save_diet_history(
                        user=user_id,
                        meal='lunch',  # You can dynamically set meal info
                        calories=user['calories'],
                        protein=user['protein'],
                        carbohydrates=user['carbohydrates'],
                        fat=user['fat'],
                        image_bytes=rotated_img,  # Save the cached image
                        db=next(get_db()),  # Assume db session is managed
                    )

                    if saved_history:
                        # Clear the user's cache after saving
                        del nutrition_cache[user_id]
                        reply_message = f"$ 記錄成功" #"\n$ 到【每餐】或【報告】查看"
                        emoji = [
                            {
                                "index": 0,
                                "productId": "5ac22b23040ab15980c9b44d",
                                "emojiId": "070"
                            },
                            # {
                            #     "index": 7,
                            #     "productId": "5ac21e6c040ab15980c9b444",
                            #     "emojiId": "020"
                            # },
                        ]
                        reply_status = await reply_with_message(reply_token, reply_message, emoji)
                        print(f"Reply status: {reply_status}")
                        return {"status": "ok"}
                    else:
                        return {"error": "Failed to save diet history"}
                else:
                    # Cache expired, inform the user
                    reply_message = "請重傳圖片"
                    reply_status = await reply_with_message(reply_token, reply_message)
                    print(f"Reply status: {reply_status}")
                    return {"status": "ok"}

            if postback_data == "action=selected_datetime_details" or postback_data == "action=selected_datetime_overview":
                await start_loading_animation(chat_id=user_id)

                selected_date_str = event["postback"]["params"]["date"]
                selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

                history_type = postback_data[25:]
                diet_history = get_diet_history_from_db(username=user_id, db=next(get_db()), filter_date=selected_date)

                if not diet_history:
                    reply_message = "找不到紀錄"
                    reply_status = await reply_with_message(reply_token, reply_message)
                    print(f"Reply status: {reply_status}")
                    return {"status": "ok"}

                if history_type == 'details':
                    reply_status = await reply_with_carousel_history(reply_token, diet_history)
                else:
                    reply_status = await reply_with_overview_history(reply_token, diet_history)
                print(f"Reply status: {reply_status}")
                return {"status": "ok"}

            if postback_data == "action=view_details" or postback_data == "action=view_overview":
                history_type = postback_data[12:]
                reply_status = await reply_with_datetime_picker_quick_reply(reply_token, history_type)
                print(f"Reply status: {reply_status}")
                return {"status": "ok"}

        # Handle image message
        if "message" in event and event["message"]["type"] == "image":
            await start_loading_animation(chat_id=user_id)

            message_id = event["message"]["id"]

            # Download the image from LINE's server
            image_bytes = await download_image(message_id)

            if image_bytes:
                nutrition_info = img_analysis(image_bytes)
                nutrition_info['calories'] = nutrition_info['protein'] * 4 + nutrition_info['carbohydrates'] * 4 + nutrition_info['fat'] * 9
                print(nutrition_info)

                compressed_image = compress_image(image_bytes)
                # Cache the user's nutrition data and compressed image
                nutrition_cache[user_id] = {
                    **nutrition_info,
                    'image': compressed_image
                }

                # Start a timer to clear the cache after 10 seconds
                asyncio.create_task(clear_cache_after_timeout(nutrition_cache, user_id, timeout=300))

                reply_status = await reply_with_bubble_nutrition(reply_token, nutrition_info)
                print(f"Reply with Flex Message sent: {reply_status}")
                return {"status": "ok"}

            else:
                reply_message = "Sorry, I couldn't process the image."
                reply_status = await reply_with_message(reply_token, reply_message)
                print(f"Reply status: {reply_status}")
                return {"status": "ok"}

        # Handle text message (echo the message)
        if "message" in event and event["message"]["type"] == "text":
            # user_message = event["message"]["text"]
            reply_message = '不支援文字對話模式'
            print(f"Received message: {reply_message}")

            # Reply to the user with the same message
            reply_status = await reply_with_message(reply_token, reply_message)
            print(f"Reply status: {reply_status}")

    return {"status": "ok"}


# Add this block to run the app when the script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6666)
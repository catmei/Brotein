import httpx
import os
from dotenv import load_dotenv
from PIL import Image
import io
import asyncio
import pytz

load_dotenv()

# LINE Messaging API endpoint and channel access token
LINE_REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CONTENT_ENDPOINT = "https://api-data.line.me/v2/bot/message/{message_id}/content"


# Function to compress the image to meet minimum resolution
def compress_image(image_bytes, max_size=(600, 400)):
    # Open the image from bytes
    image = Image.open(io.BytesIO(image_bytes))

    # Resize the image to a smaller resolution while maintaining aspect ratio
    image.thumbnail(max_size)

    # Save the image back to bytes
    compressed_image = io.BytesIO()
    image.save(compressed_image, format='JPEG', quality=85)
    return compressed_image.getvalue()


def rotate_image_if_vertical(image_bytes):
    """Rotates the image by 90 degrees if it is vertical (height > width)."""
    # Load the image from bytes
    image = Image.open(io.BytesIO(image_bytes))

    # Check if the image is vertical (height > width)
    if image.height > image.width:
        # Rotate the image by 90 degrees
        rotated_image = image.rotate(90, expand=True)
        # Save the rotated image back to bytes
        img_byte_arr = io.BytesIO()
        rotated_image.save(img_byte_arr, format=image.format)
        return img_byte_arr.getvalue()

    # If the image is not vertical, return the original image bytes
    return image_bytes


# Function to clear cache for a specific user after 10 seconds
async def clear_cache_after_timeout(user_cache, user_id, timeout=60):
    await asyncio.sleep(timeout)
    if user_id in user_cache:
        del user_cache[user_id]
        print(f"Cache cleared for user: {user_id}")


# Function to reply to the user with a message
async def reply_with_message(reply_token: str, message: str, emoji=None):
    if emoji is None:
        emoji = [
            {
                "index": 0,
                "productId": "5ac21c46040ab15980c9b442",
                "emojiId": "018"
            }
        ]
        message = f"$ {message}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": message,
                "emojis": emoji
            }
        ]

    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


async def start_loading_animation(chat_id: str, loading_seconds: int = 20):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    payload = {
        "chatId": chat_id,  # Use the user's chatId here
        "loadingSeconds": loading_seconds  # The duration of the loading animation
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.line.me/v2/bot/chat/loading/start", json=payload, headers=headers)
        return response.status_code


# Function to reply to the user with a Flex Message in receipt layout
async def reply_with_bubble_nutrition(reply_token: str, nutrition_info: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    # Flex Message payload with only '營養成分' and the footer button
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "flex",
                "altText": "營養資訊",
                "contents": {
                    "type": "bubble",
                    "size": "kilo",
                    "styles": {
                        "footer": {
                            "separator": False  # Removed the separator between body and footer
                        }
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "營養成分",  # Only showing Nutritional Info title
                                "weight": "bold",
                                "size": "xl",
                                "align": "center"
                            },
                            {
                                "type": "separator",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "蛋白質",
                                                "size": "sm",
                                                "color": "#8C8C8C",
                                                "flex": 0
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{nutrition_info['protein']} 克",  # Bold value
                                                "size": "sm",
                                                "color": "#111111",
                                                "align": "end",
                                                "weight": "bold"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "碳水化合物",
                                                "size": "sm",
                                                "color": "#8C8C8C",
                                                "flex": 0
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{nutrition_info['carbohydrates']} 克",  # Bold value
                                                "size": "sm",
                                                "color": "#111111",
                                                "align": "end",
                                                "weight": "bold"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "脂肪",
                                                "size": "sm",
                                                "color": "#8C8C8C",
                                                "flex": 0
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{nutrition_info['fat']} 克",  # Bold value
                                                "size": "sm",
                                                "color": "#111111",
                                                "align": "end",
                                                "weight": "bold"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "separator",  # Added separator between 脂肪 and 卡路里
                                        "margin": "md"
                                    },
                                    {
                                        "type": "box",
                                        "layout": "horizontal",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "卡路里",
                                                "size": "sm",
                                                "color": "#8C8C8C",
                                                "flex": 0
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{nutrition_info['calories']} 大卡",  # Bold value
                                                "size": "sm",
                                                "color": "#111111",
                                                "align": "end",
                                                "weight": "bold"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # Footer with "記錄" button in a color to match the style
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#27ACB2",  # Custom color to match the style
                                "action": {
                                    "type": "postback",
                                    "label": "記錄",
                                    "data": "action=save"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


# Function to reply with the carousel view history
async def reply_with_carousel_history(reply_token: str, diet_history: list):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    diet_history = diet_history[:10]  # max limit = 10
    # Build carousel bubbles based on the diet history
    bubbles = []
    for i, entry in enumerate(diet_history):
        utc_time = entry['datetime'].replace(tzinfo=pytz.utc)
        client_timezone = pytz.timezone('Asia/Taipei')
        local_time = utc_time.astimezone(client_timezone)
        taipei_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

        bubble = {
            "type": "bubble",
            "size": "kilo",
            "hero": {
                "type": "image",
                "url": entry['img_url'] if entry.get('img_url') else "https://via.placeholder.com/400",
                # Fallback if no image URL
                "size": "full",
                "aspectRatio": "4:3",  # Matches the aspect ratio in the example
                "aspectMode": "cover",  # Ensures the image fills the space
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    # {
                    #     "type": "text",
                    #     "text": entry['meal'].capitalize(),
                    #     "size": "xl",
                    #     "weight": "bold"
                    # },
                    {
                        "type": "text",
                        "text": taipei_time,
                        "size": "xs",
                        "color": "#aaaaaa"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "蛋白質",
                                        "size": "sm",
                                        "color": "#8C8C8C",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{entry['protein']} 克",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "碳水化合物",
                                        "size": "sm",
                                        "color": "#8C8C8C",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{entry['carbohydrates']} 克",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "脂肪",
                                        "size": "sm",
                                        "color": "#8C8C8C",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{entry['fat']} 克",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "卡路里",
                                        "size": "sm",
                                        "color": "#8C8C8C",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{entry['calories']} 大卡",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
        }
        bubbles.append(bubble)

    # Create the Flex Message with the carousel containing the bubbles
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "flex",
                "altText": "View History",
                "contents": {
                    "type": "carousel",
                    "contents": bubbles  # Insert the bubbles into the carousel
                }
            }
        ]
    }
    # Send the message to LINE API
    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


async def reply_with_overview_history(reply_token: str, diet_history: list):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    # Start the table with the date as the title
    taipei_tz = pytz.timezone('Asia/Taipei')
    utc_time = diet_history[0]['datetime'].replace(tzinfo=pytz.utc)
    local_time = utc_time.astimezone(taipei_tz)
    report_date = local_time.strftime("%Y-%m-%d")
    diet_history = diet_history[:10]
    diet_history = diet_history[::-1]

    # Initialize the total values
    total_protein = 0
    total_carbohydrates = 0
    total_fat = 0
    total_calories = 0

    # Create a formatted summary for each meal entry
    meal_entries = []
    for entry in diet_history:
        # Add the current entry's values to the total
        total_protein += entry['protein']
        total_carbohydrates += entry['carbohydrates']
        total_fat += entry['fat']
        total_calories += entry['calories']

        # Add each meal as a row in the report
        meal_entries.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "image",
                    "url": entry['img_url'] if entry.get('img_url') else "https://via.placeholder.com/100",
                    "size": "xxs",
                    "aspectMode": "cover",
                    "aspectRatio": "1:1"
                },
                {
                    "type": "text",
                    "text": f"{entry['protein']}",
                    "size": "sm",
                    "flex": 1,
                    "align": "center",
                    "gravity": "center"
                },
                {
                    "type": "text",
                    "text": f"{entry['carbohydrates']}",
                    "size": "sm",
                    "flex": 1,
                    "align": "center",
                    "gravity": "center"
                },
                {
                    "type": "text",
                    "text": f"{entry['fat']}",
                    "size": "sm",
                    "flex": 1,
                    "align": "center",
                    "gravity": "center"
                },
                {
                    "type": "text",
                    "text": f"{entry['calories']}",
                    "size": "sm",
                    "flex": 1,
                    "align": "center",
                    "gravity": "center"
                }
            ],
            "spacing": "md"
        })

    # Add a separator before the total values
    meal_entries.append({
        "type": "separator",
        "margin": "md"
    })

    # Add the totals row at the end
    meal_entries.append({
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": "總計",  # "Total" in Chinese
                "size": "sm",
                "flex": 1,
                "align": "center",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": f"{total_protein}",
                "size": "sm",
                "flex": 1,
                "align": "center",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": f"{total_carbohydrates}",
                "size": "sm",
                "flex": 1,
                "align": "center",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": f"{total_fat}",
                "size": "sm",
                "flex": 1,
                "align": "center",
                "weight": "bold"
            },
            {
                "type": "text",
                "text": f"{total_calories}",
                "size": "sm",
                "flex": 1,
                "align": "center",
                "weight": "bold"
            }
        ],
        "spacing": "md"
    })

    # Create a single bubble for the overview report with the new format
    bubble = {
        "type": "bubble",
        "size": "mega",  # Larger size to accommodate the format
        "header": {  # This section acts as the header and covers the full top area
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"🗒️  {report_date}  🗒️",  # Date with "記錄"
                    "size": "xl",
                    "weight": "bold",
                    "color": "#ffffff",  # White text for contrast
                    "align": "center"
                }
            ],
            "backgroundColor": "#27ACB2",  # Set the background color to cover the top space
            "paddingTop": "19px",  # Adjust the padding as needed
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "   ", "size": "sm", "align": "center", "weight": "bold"},
                        {"type": "text", "text": "蛋白", "size": "sm", "align": "center", "weight": "bold"},
                        {"type": "text", "text": "碳水", "size": "sm", "align": "center", "weight": "bold"},
                        {"type": "text", "text": "脂肪", "size": "sm", "align": "center", "weight": "bold"},
                        {"type": "text", "text": "熱量", "size": "sm", "align": "center", "weight": "bold"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "相片", "size": "sm", "align": "center", "weight": "bold"},
                        {"type": "text", "text": "(克)", "size": "xs", "align": "center", "color": "#aaaaaa"},
                        {"type": "text", "text": "(克)", "size": "xs", "align": "center", "color": "#aaaaaa"},
                        {"type": "text", "text": "(克)", "size": "xs", "align": "center", "color": "#aaaaaa"},
                        {"type": "text", "text": "(大卡)", "size": "xs", "align": "center", "color": "#aaaaaa"}
                    ]
                },
                {
                    "type": "separator",
                    "margin": "sm"
                },
                *meal_entries  # Add all meal rows here
            ]
        }
    }

    # Create the Flex Message with a single bubble
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "flex",
                "altText": "Diet Overview Report",
                "contents": bubble
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


async def reply_with_view_history_options(reply_token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "$ 點擊下方 \n      【🗒️細項】或【🗒️總覽】",
                "emojis": [
                    {
                        "index": 0,
                        "productId": "5ac21e6c040ab15980c9b444",
                        "emojiId": "020"
                    },
                ],
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "🗒️細項",
                                "data": "action=view_details"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "🗒️總覽",
                                "data": "action=view_overview"
                            }
                        }
                    ]
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


# Function to download an image from LINE's server
async def download_image(message_id: str):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    image_url = LINE_CONTENT_ENDPOINT.format(message_id=message_id)

    async with httpx.AsyncClient() as client:
        response = await client.get(image_url, headers=headers)
        if response.status_code == 200:
            return response.content  # Return the image as bytes
        return None


# Function to reply with a quick reply (camera action)
async def reply_with_camera_quick_reply(reply_token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "$ 點擊下方【📷拍照/相簿】",
                "emojis": [
                    {
                        "index": 0,
                        "productId": "5ac21e6c040ab15980c9b444",
                        "emojiId": "020"
                    },
                    # {
                    #     "index": 13,
                    #     "productId": "5ac2216f040ab15980c9b448",
                    #     "emojiId": "001"
                    # },
                ],
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "camera",
                                "label": "拍照/相簿"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "取消",
                                "data": "action=cancel"
                            }
                        }
                    ]
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code


# Function to reply with a datetime picker as a quick reply
async def reply_with_datetime_picker_quick_reply(reply_token: str, history_type: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "$ 點擊下方【🕓選擇時間】",
                "emojis": [
                    {
                        "index": 0,
                        "productId": "5ac21e6c040ab15980c9b444",
                        "emojiId": "020"
                    }
                ],
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "datetimepicker",
                                "data": f"action=selected_datetime_{history_type}",
                                "label": "🕓選擇時間",
                                "mode": "date"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "postback",
                                "label": "取消",
                                "data": "action=cancel"
                            }
                        }
                    ]
                }
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(LINE_REPLY_ENDPOINT, json=payload, headers=headers)
        return response.status_code

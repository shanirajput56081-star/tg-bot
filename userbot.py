import os
import asyncio
import json
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButtonCallback
import threading

# =============================================
#   RAILWAY USERBOT - config
#   Railway pe Environment Variables mein set karo
# =============================================

API_ID      = int(os.environ.get('API_ID', 0))
API_HASH    = os.environ.get('API_HASH', '')
PHONE       = os.environ.get('PHONE_NUMBER', '')
TARGET_BOT  = os.environ.get('TARGET_BOT', '@Truecallerssbot')
API_KEY     = os.environ.get('API_KEY', 'secret123')   # PHP se match karna chahiye
PORT        = int(os.environ.get('PORT', 5000))
BUTTON_TEXT = os.environ.get('BUTTON_TEXT', 'View full details')  # Button ka exact text

app    = Flask(__name__)
client = TelegramClient('session', API_ID, API_HASH)
loop   = asyncio.new_event_loop()

# =============================================
#   MAIN FUNCTION - Bot se baat karo
# =============================================

async def fetch_from_bot(number):
    try:
        # Step 1: Target bot ko number bhejo
        await client.send_message(TARGET_BOT, number)
        print(f"[✓] Sent to bot: {number}")

        # Step 2: Bot ka pehla reply wait karo (button wala)
        await asyncio.sleep(4)

        messages = await client.get_messages(TARGET_BOT, limit=3)
        button_msg = None

        for msg in messages:
            if not msg.out and msg.buttons:
                button_msg = msg
                break

        if not button_msg:
            # Shayad seedha text reply aaya ho
            for msg in messages:
                if not msg.out and msg.text:
                    return msg.text
            return "❌ Bot ne koi reply nahi diya."

        print(f"[✓] Button message mila!")

        # Step 3: "View full details" button dhundo aur click karo
        clicked = False
        for row in button_msg.buttons:
            for btn in row:
                if BUTTON_TEXT.lower() in btn.text.lower():
                    await btn.click()
                    clicked = True
                    print(f"[✓] Button clicked: {btn.text}")
                    break
            if clicked:
                break

        if not clicked:
            # Koi bhi button click karo (pehla)
            await button_msg.buttons[0][0].click()
            print("[!] Default button clicked")

        # Step 4: Button click ke baad reply wait karo
        await asyncio.sleep(5)

        messages2 = await client.get_messages(TARGET_BOT, limit=3)
        for msg in messages2:
            if not msg.out and msg.text and msg.id > button_msg.id:
                return msg.text

        # Agar naya message nahi aaya toh pehla wala return karo
        return button_msg.text or "⚠️ Result nahi mila."

    except Exception as e:
        print(f"[✗] Error: {e}")
        return f"❌ Error: {str(e)}"


# =============================================
#   FLASK API ENDPOINT
# =============================================

@app.route('/fetch', methods=['POST'])
def fetch():
    # API Key check
    key = request.headers.get('X-API-Key', '')
    if key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    data   = request.get_json()
    number = data.get('number', '').strip()

    if not number:
        return jsonify({'error': 'Number missing'}), 400

    print(f"[→] Request: {number}")

    # Async function ko sync mein run karo
    future = asyncio.run_coroutine_threadsafe(fetch_from_bot(number), loop)
    result = future.result(timeout=30)

    print(f"[←] Result: {result[:80]}")
    return jsonify({'result': result})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'bot': TARGET_BOT})


# =============================================
#   START
# =============================================

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def start_client():
    await client.start(phone=PHONE)
    print("[✓] Telegram client connected!")

if __name__ == '__main__':
    # Background event loop start karo
    t = threading.Thread(target=start_loop, args=(loop,), daemon=True)
    t.start()

    # Telegram client connect karo
    future = asyncio.run_coroutine_threadsafe(start_client(), loop)
    future.result(timeout=60)

    print(f"[✓] Flask server starting on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)

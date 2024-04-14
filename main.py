import aiohttp, asyncio, json, random
from datetime import datetime
from modules.console import Logger

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()
    
with open("config.json", "r") as f:
    config = json.load(f)

async def username(session, user_id):
    while True:
        response = await fetch(session, f"https://users.roblox.com/v1/users/{user_id}")
        if "name" in response:
            return response["name"]
        elif "status" in response and response["status"] == 429:
            await asyncio.sleep(1)
            Logger.error(f"Ratelimited | User ID: {user_id}")
        else:
            Logger.error(f"Username not found | User ID: {user_id}")
            return None

async def created(session, user_id):
    while True:
        response = await fetch(session, f"https://users.roblox.com/v1/users/{user_id}")
        if "created" in response:
            created_date = response["created"]
            datetime_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]
            for format_str in datetime_formats:
                try:
                    created_year = datetime.strptime(created_date, format_str).year
                    return created_year
                except ValueError:
                    continue
            Logger.error(f"Unable to get creation date | User ID: {user_id}")
            return None
        elif "status" in response and response["status"] == 429:
            await asyncio.sleep(1)
            Logger.error(f"Ratelimited | User ID: {user_id}")
        else:
            Logger.error(f"Unable to get creation date | User ID: {user_id}")
            return None

async def avatar_thumbnail(session, user_id):
    response = await fetch(session, f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=250x250&format=Png&isCircular=true")
    return response["data"][0]["imageUrl"] if "data" in response else None

async def verified(session, user_id, asset_ids):
    verified_assets = []
    for asset_id in asset_ids:
        while True:
            response = await fetch(session, f"https://inventory.roblox.com/v1/users/{user_id}/items/Asset/{asset_id}")
            if "data" in response and response["data"]:
                verified_assets.append(asset_id)
                break
            elif "status" in response and response["status"] == 429:
                await asyncio.sleep(1)
                Logger.error(f"Ratelimited | User ID: {user_id}")
            else:
                break
    return verified_assets if verified_assets else None

async def last_online(session, user_id):
    payload = {"userIds": [user_id]}
    while True:
        response = await session.post("https://presence.roblox.com/v1/presence/last-online", json=payload)
        response_data = await response.json()
        if "lastOnlineTimestamps" in response_data:
            last_online_timestamps = response_data["lastOnlineTimestamps"]
            if last_online_timestamps:
                last_online = last_online_timestamps[0].get("lastOnline")
                if last_online:
                    datetime_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]
                    for format_str in datetime_formats:
                        try:
                            last_online_datetime = datetime.strptime(last_online, format_str)
                            return last_online_datetime
                        except ValueError:
                            continue
            Logger.error(f"Unable to get last online date | User ID: {user_id}")
            return None
        elif "status" in response_data and response_data["status"] == 429:
            await asyncio.sleep(1)
            Logger.error(f"Ratelimited | User ID: {user_id}")
        else:
            Logger.error(f"Unable to get last online date | User ID: {user_id}")
            return None

async def rap(session, user_id, cursor, rap=0):
    response = await fetch(session, f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=100&cursor={cursor}")
    if "data" in response:
        for i in response["data"]:
            if "recentAveragePrice" in i and i["recentAveragePrice"] is not None:
                rap += i["recentAveragePrice"]
    if "nextPageCursor" in response and response["nextPageCursor"] is not None:
        return await rap(session, user_id, response["nextPageCursor"], rap)
    return rap

async def main(webhook_url, min_id, max_id):
    async with aiohttp.ClientSession() as session:
        user_id = random.randint(min_id, max_id)

        asset_ids_to_check = [18824203, 1567446, 93078560, 102611803]
        verified_assets = []

        for asset_id in asset_ids_to_check:
            assets = await verified(session, user_id, [asset_id])
            if assets:
                verified_assets.extend(assets)

        user_rap = await rap(session, user_id, "", 0)
        roblox_username = await username(session, user_id)
        created_year = await created(session, user_id)
        last_online_date = await last_online(session, user_id)
        verified_status = bool(verified_assets)

        if created_year is None:
            Logger.error(f"Unable to get creation date | User ID: {user_id}")
            return

        if last_online_date is None:
            Logger.error(f"Unable to get last online date | User ID: {user_id}")
            return

        offline_years = config.get("offline_years")

        if last_online_date.year > datetime.now().year - offline_years:
            Logger.error(f"Account has been online within the last {offline_years} years")
            return

        created_year_str = str(created_year)
        last_online_date_str = last_online_date.strftime("%B %d, %Y")

        embed = {
            "title": f"✅ New possible password guess!",
            "description": "⭐ https://github.com/zkoolmao/Roblox-PG-Assistant",
            "color": 5763719,
            "url": f"https://roblox.com/users/{user_id}",
            "thumbnail": {"url": await avatar_thumbnail(session, user_id)},
            "fields": [
                {"name": "User ID:", "value": user_id, "inline": True},
                {"name": "Username:", "value": roblox_username, "inline": True},
                {"name": "Created Year:", "value": created_year_str, "inline": True},
                {"name": "Last Online:", "value": last_online_date_str, "inline": True},
                {"name": "Verified:", "value": verified_status, "inline": True},
                {"name": "Total RAP:", "value": user_rap, "inline": True},
                {"name": "Common Passwords:", "value": f"{roblox_username}123, {roblox_username}{created_year_str}, {roblox_username}s123", "inline": True}
            ]
        }

        data = {"embeds": [embed]}
        async with session.post(webhook_url, json=data) as response:
            if response.status == 204:
                Logger.info(f"Successfully sent {roblox_username} to webhook")
            else:
                Logger.error(f"Failed to send {roblox_username} to webhook | Status Code: {response.status}")

async def run():
    webhook = config.get("webhook_url")
    min_id = config.get("min_id")
    max_id = config.get("max_id")

    while True:
        try:
            await main(webhook, min_id, max_id)
        except Exception as e:
            Logger.error(f"An error occurred: {e}")
        await asyncio.sleep(1)

async def setup():
    await run()

if __name__ == "__main__":
    asyncio.run(setup())
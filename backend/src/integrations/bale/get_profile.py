import base64

import requests


def get_bale_profile_photo_url(
    token: str,
    user_id: int,
) -> str | None:
    """
    Fetch Bale user profile photo as a base64 data URI.

    Downloads the image server-side so the LLM provider never needs to
    fetch the Bale URL (which contains the bot token and may be unreachable
    from the provider's network).

    Returns:
        str | None: data URI string  (data:image/jpeg;base64,...)
    """

    try:
        chat_resp = requests.get(
            f"https://tapi.bale.ai/bot{token}/getChat",
            params={"chat_id": user_id},
            timeout=10,
        ).json()

        photo = chat_resp.get("result", {}).get("photo", {})
        file_id = photo.get("big_file_id")
        if not file_id:
            return None

        file_resp = requests.get(
            f"https://tapi.bale.ai/bot{token}/getFile",
            params={"file_id": file_id},
            timeout=10,
        ).json()

        file_path = file_resp.get("result", {}).get("file_path")
        if not file_path:
            return None

        download_url = f"https://tapi.bale.ai/file/bot{token}/{file_path}"
        image_resp = requests.get(download_url, timeout=15)
        image_resp.raise_for_status()

        content_type = image_resp.headers.get("content-type", "").split(";")[0].strip()
        if not content_type or content_type == "application/octet-stream":
            content_type = "image/jpeg"
        b64 = base64.b64encode(image_resp.content).decode("ascii")
        return f"data:{content_type};base64,{b64}"

    except Exception as e:
        print("get_bale_profile_photo_url error:", e)
        return None
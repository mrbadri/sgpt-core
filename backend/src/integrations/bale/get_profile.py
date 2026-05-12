import requests


def get_bale_profile_photo_url(
    token: str,
    user_id: int,
) -> str | None:
    """
    Fetch Bale user profile photo download URL.

    Returns:
        str | None: downloadable profile image URL
    """

    try:
        # Step 1: get chat info
        chat_resp = requests.get(
            f"https://tapi.bale.ai/bot{token}/getChat",
            params={
                "chat_id": user_id,
            },
            timeout=10,
        ).json()

        photo = (
            chat_resp
            .get("result", {})
            .get("photo", {})
        )

        file_id = photo.get("big_file_id")

        if not file_id:
            return None

        # Step 2: get file info
        file_resp = requests.get(
            f"https://tapi.bale.ai/bot{token}/getFile",
            params={
                "file_id": file_id,
            },
            timeout=10,
        ).json()

        file_path = (
            file_resp
            .get("result", {})
            .get("file_path")
        )

        if not file_path:
            return None

        # Step 3: build download url
        return (
            f"https://tapi.bale.ai/file/bot{token}/{file_path}"
        )

    except Exception as e:
        print("get_bale_profile_photo_url error:", e)
        return None
import json

from aiogram.types import MediaGroup


def json_to_media_group(json_data: str) -> MediaGroup:
    media_group_data = json.loads(json_data)

    media_group = MediaGroup()

    for item in media_group_data:
        media_type = item.get("type")
        media = item.get("media")
        caption = item.get("caption")

        if media_type == "photo":
            media_group.attach_photo(media, caption=caption)
        elif media_type == "video":
            media_group.attach_video(media, caption=caption)
        elif media_type == "audio":
            media_group.attach_audio(media, caption=caption)
        elif media_type == "document":
            media_group.attach_document(media, caption=caption)

    return media_group


def media_group_to_json(media_group: MediaGroup) -> str:
    media_group_data = [
        {
            "media": item.media,
            "type": item.type,
            "caption": getattr(item, "caption", None)
        }
        for item in media_group.media
    ]
    return json.dumps(media_group_data, ensure_ascii=False)
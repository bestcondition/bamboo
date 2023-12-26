import mimetypes
from pathlib import Path

from apiflask import APIBlueprint
from flask import current_app
from werkzeug.datastructures import FileStorage

from bamboo.database import db
from bamboo.database.models import Media
from bamboo.jobs import gen_small_image
from bamboo.schemas.media import IMAGE_SUFFIXES, MediaSchema
from bamboo.utils import gen_uuid

media_bp = APIBlueprint("media", __name__)


@media_bp.post("/")
@media_bp.input(MediaSchema, location="files")
def upload_media(files_data: dict) -> dict | tuple[dict, int]:
    file: FileStorage = files_data["file"]
    upload_filename: str = file.filename  # pyright: ignore reportGeneralTypeIssues
    content_type = mimetypes.guess_type(upload_filename)[0]
    filename = f"{gen_uuid()}_{upload_filename}"
    media_dir = Path(current_app.config["BAMBOO_MEDIA_DIR"])
    media_file = media_dir / filename
    file.save(media_file)
    file_suffix = media_file.suffix.lower()
    if file_suffix in IMAGE_SUFFIXES:
        # async generate small image
        gen_small_image.queue(filename)  # pyright: ignore reportFunctionMemberAccess
    media = Media(content_type=content_type, path=filename)
    db.session.add(media)
    db.session.commit()
    return {
        "id": media.id,
        "path": media.path,
    }

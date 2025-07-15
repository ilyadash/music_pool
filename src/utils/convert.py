import asyncio
import os
from pydub import AudioSegment
from pydub.utils import mediainfo

async def convert_to_mp3(file_dir: str, file_name: str) -> str:
    full_path = os.path.join(file_dir, file_name)

    name, _  = await asyncio.to_thread(os.path.splitext, file_name)
    tags     = await asyncio.to_thread(lambda: mediainfo(full_path).get('TAG', {}))
    audio    = await asyncio.to_thread(AudioSegment.from_file, full_path)
    output   = os.path.join(file_dir, f"{name}.mp3")

    # export in thread, with kwargs
    await asyncio.to_thread(audio.export, output, format="mp3", tags=tags)
    return output

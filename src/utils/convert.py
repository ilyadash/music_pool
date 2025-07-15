import os
from pydub import AudioSegment
from pydub.utils import mediainfo

def convert_to_mp3(file_dir: str = '', file_name: str = ''):
    convertable_extensions: list[str] = ['.m4a']
    name, extension = os.path.splitext(file_name)
    if extension in convertable_extensions:
        audio = AudioSegment.from_file(file_dir+'\\'+file_name)
        audio.export(file_dir+'\\'+name+".mp3", format="mp3", tags=mediainfo(file_dir+'\\'+file_name)['TAG'])
        

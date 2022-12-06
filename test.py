from epub2note import Epub2note
import os
note = Epub2note(notebook_name='我的图书')

for file in os.listdir():
    if '.epub' in file:
        print('gen ->',file)
        note.gen_note(epub_path=file,merge=True)
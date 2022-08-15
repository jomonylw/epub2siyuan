from epub2note import Epub2note
import os
note = Epub2note(notebook_name='我的图书')

for f in os.listdir():
    if '.epub' in f:
        print('gen ->',f)
        note.gen_note(epub_path=f)
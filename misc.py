

def is_note_black(note):
    # check if note is black based on its index starting from C0
    note = note % 12
    return note in [1, 3, 6, 8, 10]
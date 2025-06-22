import random
import string


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choices(letters, k=length))

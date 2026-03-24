# test_audio.py
from functions import get_client

TOKEN = "h8Se9s3Nayqmu3i2KQ9qYjueTvudoeJxscon1c7wnOU.qD5UBrSZqxuC44dkcWiJJLt42zc"  # copie do /debug-token
sp = get_client(TOKEN)
track_id = "4Dvkj6JhhA12EX05fT7y2e"  # ou outro ID válido
features = sp.audio_features(tracks=[track_id])
print(features)
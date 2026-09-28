from bpbot.db import readings_repo as repo
from bpbot.services.classification import classify

FAKE_USER = 999_999_999

saved = repo.insert_reading(FAKE_USER, 135, 85, 72, classify(135, 85), "morning")
print("inserted:", saved)

print("recent:", repo.get_recent(FAKE_USER))

print("deleted:", repo.delete_latest(FAKE_USER))
print("after delete:", repo.get_recent(FAKE_USER))
print("delete on empty:", repo.delete_latest(FAKE_USER))

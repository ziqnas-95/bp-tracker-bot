from bpbot.db import dedup_repo

FAKE_UPDATE_ID = 999999001

print("first time:", dedup_repo.mark_processed_if_new(FAKE_UPDATE_ID))  # True
print("second time:", dedup_repo.mark_processed_if_new(FAKE_UPDATE_ID))  # False
print("different id:", dedup_repo.mark_processed_if_new(FAKE_UPDATE_ID + 1))  # True

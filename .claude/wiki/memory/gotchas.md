# Known Bugs Gotchas

> Fix bug add entry. Fix edge case add entry. Bug return look new check here. Stop future confuse.

## Entry Format

```
## [YYYY-MM-DD] Title
- Symptom: What break.
- Cause: Why break.
- Fix/Workaround: How fix. How avoid.
- Files/Area: Where look.
```

---

<!-- Example. Drop write real. -->

## [2026-01-20] Example: Dev timeout
- **Symptom**: Request X timeout. Break local only. Prod OK.
- **Cause**: Dev service Y run slow mock. Mock lack cache.
- **Fix/Workaround**: Set env `MOCK_CACHE=1`. Enable local cache.
- **Files/Area**: `services/y_client.py`
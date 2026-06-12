# Repository API Guide

## 1. Version Check Endpoint

Used by client apps or tweaks to check whether a newer package version is available in the repo.

### Request

```text
GET https://repo.example.com/api/version.json
```

### Response

```json
{
  "com.example.package": {
    "version": "1.2.3",
    "date": "2026-06-11 22:45",
    "name": "Example Package"
  }
}
```

### Fields

| Field | Type | Description |
|------|------|------|
| `version` | string | Latest version published in the repo |
| `date` | string | Last compile time in `YYYY-MM-DD HH:MM` format |
| `name` | string | Package display name |

### Client Logic

```text
1. GET https://repo.example.com/api/version.json
2. Read response[MY_BUNDLE_ID]
3. If missing, treat it as unavailable or network failure
4. If response[MY_BUNDLE_ID].version > local version, show an update entry
5. Otherwise, hide the update entry
```

### Version Comparison Note

Do not compare semantic versions as raw strings. Split by `.` and compare numeric segments.

```objc
- (BOOL)isNewerVersion:(NSString *)remote than:(NSString *)local {
    NSArray *r = [remote componentsSeparatedByString:@"."];
    NSArray *l = [local componentsSeparatedByString:@"."];
    NSUInteger count = MAX(r.count, l.count);
    for (NSUInteger i = 0; i < count; i++) {
        NSInteger rv = (i < r.count) ? [r[i] integerValue] : 0;
        NSInteger lv = (i < l.count) ? [l[i] integerValue] : 0;
        if (rv > lv) return YES;
        if (rv < lv) return NO;
    }
    return NO;
}
```

---

## 2. Package Download URL

The default package URL format is:

```text
https://repo.example.com/pkg/<bundle_id>.deb
```

Example:

```text
https://repo.example.com/pkg/com.example.package.deb
```

---

## 3. Suggested Update Flows

### Option A: Download and Share

This is the most portable approach.

```text
1. Download https://repo.example.com/pkg/<bundle_id>.deb
2. Save it into a temporary directory
3. Present a share sheet or open-in menu
```

### Option B: Open in Sileo

```text
sileo://package/<bundle_id>
```

### Option C: Open in Cydia

```text
cydia://package/<bundle_id>
```

### Option D: Long-Press Menu

| Interaction | Action |
|------|------|
| Tap | Open in preferred package manager |
| Long press | Show download / share / manager-specific actions |

---

## 4. UI Recommendation

A compact update row can display:

```text
v1.2.3 available · 2026-06-11
Tap to update · Long press for more options
```

- Show it only when a newer version is available.
- Keep it hidden when already up to date.

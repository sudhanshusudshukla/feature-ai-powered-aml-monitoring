# Deliverability Fixes - Round 2

## Fix Applied

### [BLOCKER] packaging — Backend service preview port configuration

**File:** `docker-compose.yml`

**Change:** Replaced `expose: - "8000"` with `ports: - "8000:8000"` for the backend service while keeping `x-preview-port: 8000`

**Root cause:** The backend service had `x-preview-port: 8000` annotation but used `expose:` instead of `ports:`, which means the port was only accessible between containers, not published to the host. The preview infrastructure requires a published port to create a Service and route traffic to it.

**Verification:**
```bash
$ grep -A 1 '    ports:' docker-compose.yml | head -4
    ports:
      - "8000:8000"
--
    ports:
```

The backend service now publishes port 8000 on both the host and container side (`8000:8000`), matching the `x-preview-port: 8000` annotation. This allows the preview to create a Service for the backend and route traffic to it.

---

## Summary

Fixed the single blocker by publishing port 8000 for the backend service in docker-compose.yml. The service now has `ports: ["8000:8000"]` with `x-preview-port: 8000`, enabling the preview infrastructure to route traffic to the backend. The frontend service already had correct port configuration (`ports: ["80:80"]` with `x-preview-port: 80`).

No cleanup was required as this was purely a configuration fix with no scaffolding or verification files created.

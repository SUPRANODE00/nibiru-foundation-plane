# THE HORNS OF THE JINN

Consolidated production substrate for session authorization, active tamper audits, and calendar hook automation.

## Core Infrastructure Objectives
* **Creator & Administrator:** D3M13N ✶ CAPSULECRAFT
* **Default Handles Locked:** SUPRANODE00
* **Database Driver:** Local JSON-Encapsulated State Matrix (Bypassing native SQLite build overhead).

## Administrative Pipeline Handshaking
Token authorization required for deep system access; all mutations are fully hash-chained and logged.
```bash
H="Authorization: Bearer \$ADMIN_TOKEN"
curl -H "\$H" localhost:3000/api/admin/members
curl -H "\$H" localhost:3000/api/admin/telemetry
```

## Setup & Deployment
```bash
npm install
sh start.sh
```
Open local deployment port: http://localhost:3000

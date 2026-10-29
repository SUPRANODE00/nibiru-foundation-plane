const express = require('express');
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const app = express();
const PORT = process.env.PORT || 8080;

const dbFolder = path.join(__dirname, 'database');
const dbPath = path.join(dbFolder, 'members.db');

if (!fs.existsSync(dbFolder)) {
    fs.mkdirSync(dbFolder, { recursive: true });
}

const db = new Database(dbPath);
const schema = fs.readFileSync(path.join(dbFolder, 'schema.sql'), 'utf8');
db.exec(schema);

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

function isWithinDays(date, days) {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now - target;
    return diffMs <= days * 24 * 60 * 60 * 1000;
}

function canChangeUsername(member) {
    const now = new Date();
    const createdAt = new Date(member.created_at);
    const lastChanged = member.username_last_changed ? new Date(member.username_last_changed) : null;

    if (member.username_change_count === 0 && isWithinDays(createdAt, 30)) {
        return true;
    }

    if (lastChanged && (now - lastChanged) >= 90 * 24 * 60 * 60 * 1000) {
        return true;
    }

    return false;
}

app.get('/api/health', (req, res) => {
    res.json({ ok: true, name: 'NIBIRU Foundation Plane' });
});

app.get('/api/member/:id', (req, res) => {
    const member = db.prepare('SELECT * FROM members WHERE id = ?').get(req.params.id);
    if (!member) return res.status(404).json({ error: 'Member not found' });
    res.json(member);
});

app.post('/api/member', (req, res) => {
    const { handle, username, email, phone, theory_notes } = req.body || {};

    if (!handle || !username) {
        return res.status(400).json({ error: 'handle and username are required' });
    }

    try {
        const result = db.prepare(`
            INSERT INTO members (handle, username, email, phone, theory_notes)
            VALUES (?, ?, ?, ?, ?)
        `).run(handle, username, email || '', phone || '', theory_notes || '');

        const member = db.prepare('SELECT * FROM members WHERE id = ?').get(result.lastInsertRowid);
        res.status(201).json(member);
    } catch (err) {
        if (String(err).includes('UNIQUE constraint failed')) {
            return res.status(409).json({ error: 'Handle already exists' });
        }
        return res.status(500).json({ error: 'Unable to create member' });
    }
});

app.post('/api/member/:id/username', (req, res) => {
    const { username } = req.body || {};
    if (!username) {
        return res.status(400).json({ error: 'username is required' });
    }

    const member = db.prepare('SELECT * FROM members WHERE id = ?').get(req.params.id);
    if (!member) {
        return res.status(404).json({ error: 'Member not found' });
    }

    if (!canChangeUsername(member)) {
        return res.status(403).json({
            error: 'Username change not allowed yet. The policy permits one change in the first 30 days, then each subsequent change requires a 90-day cooldown.'
        });
    }

    const now = new Date().toISOString();
    const updated = db.prepare(`
        UPDATE members
        SET username = ?, username_last_changed = ?, username_change_count = username_change_count + 1
        WHERE id = ?
    `).run(username, now, req.params.id);

    if (!updated.changes) {
        return res.status(500).json({ error: 'Update failed' });
    }

    const fresh = db.prepare('SELECT * FROM members WHERE id = ?').get(req.params.id);
    res.json({ message: 'Username updated', member: fresh });
});

app.listen(PORT, () => {
    console.log(`NIBIRU app running at http://localhost:${PORT}`);
});

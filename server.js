const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

const dbFolder = path.join(__dirname, 'database');
const dbPath = path.join(dbFolder, 'members.json');

if (!fs.existsSync(dbFolder)) {
    fs.mkdirSync(dbFolder, { recursive: true });
}

// Simple Pure JS File Database Initialization
if (!fs.existsSync(dbPath)) {
    fs.writeFileSync(dbPath, JSON.stringify({ members: [], lastID: 0 }), 'utf8');
}

function readData() {
    return JSON.parse(fs.readFileSync(dbPath, 'utf8'));
}

function writeData(data) {
    fs.writeFileSync(dbPath, JSON.stringify(data, null, 2), 'utf8');
}

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
    const data = readData();
    const member = data.members.find(m => m.id === parseInt(req.params.id));
    if (!member) return res.status(404).json({ error: 'Member not found' });
    res.json(member);
});

app.post('/api/member', (req, res) => {
    const { handle, username, email, phone, theory_notes } = req.body || {};

    if (!handle || !username) {
        return res.status(400).json({ error: 'handle and username are required' });
    }

    const data = readData();
    const exists = data.members.some(m => m.handle.toLowerCase() === handle.toLowerCase());
    if (exists) {
        return res.status(409).json({ error: 'Handle already exists' });
    }

    data.lastID += 1;
    const newMember = {
        id: data.lastID,
        handle,
        username,
        email: email || '',
        phone: phone || '',
        created_at: new Date().toISOString(),
        username_last_changed: null,
        username_change_count: 0,
        status: 'active',
        theory_notes: theory_notes || ''
    };

    data.members.push(newMember);
    writeData(data);
    res.status(201).json(newMember);
});

app.post('/api/member/:id/username', (req, res) => {
    const { username } = req.body || {};
    if (!username) {
        return res.status(400).json({ error: 'username is required' });
    }

    const data = readData();
    const memberIndex = data.members.findIndex(m => m.id === parseInt(req.params.id));
    if (memberIndex === -1) {
        return res.status(404).json({ error: 'Member not found' });
    }

    const member = data.members[memberIndex];
    if (!canChangeUsername(member)) {
        return res.status(403).json({
            error: 'Username change not allowed yet. Policy limits changes.'
        });
    }

    member.username = username;
    member.username_last_changed = new Date().toISOString();
    member.username_change_count += 1;

    data.members[memberIndex] = member;
    writeData(data);

    res.json({ message: 'Username updated', member });
});

app.listen(PORT, () => {
    console.log(`NIBIRU app running at http://localhost:${PORT}`);
});

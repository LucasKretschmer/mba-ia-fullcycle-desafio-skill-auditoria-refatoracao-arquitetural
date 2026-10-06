const sqlite3 = require('sqlite3');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../config/constants');

const SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, pass TEXT)",
    "CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)",
    "CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, course_id INTEGER REFERENCES courses(id))",
    "CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE, amount REAL, status TEXT)",
    "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)",
];

function open(path) {
    return new Promise((resolve, reject) => {
        const db = new sqlite3.Database(path, (err) => (err ? reject(err) : resolve(db)));
    });
}

function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    // Uma única conexão: transações são enfileiradas para que um BEGIN nunca abra dentro de outro.
    let queue = Promise.resolve();
    const transaction = (work) => {
        const execute = async () => {
            await run('BEGIN');
            try {
                const result = await work();
                await run('COMMIT');
                return result;
            } catch (err) {
                await run('ROLLBACK');
                throw err;
            }
        };
        const result = queue.then(execute);
        queue = result.catch(() => {});
        return result;
    };

    return { run, get, all, transaction };
}

async function seed(db) {
    const { total } = await db.get("SELECT COUNT(*) AS total FROM users");
    if (total > 0) return;

    await db.transaction(async () => {
        await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", ['Leonan', 'leonan@fullcycle.com.br', await hashPassword('123')]);
        await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
        await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)", [PAYMENT_STATUS.PAID]);
    });
}

async function createDatabase(path) {
    const db = wrap(await open(path));
    await db.run('PRAGMA foreign_keys = ON');
    for (const statement of SCHEMA) {
        await db.run(statement);
    }
    await seed(db);
    return db;
}

module.exports = { createDatabase };

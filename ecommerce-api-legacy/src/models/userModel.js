function createUserModel(db) {
    return {
        findByEmail: (email) => db.get("SELECT id FROM users WHERE email = ?", [email]),
        create: async (name, email, passwordHash) => {
            const { lastID } = await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, passwordHash]);
            return lastID;
        },
        // Matrículas e pagamentos saem junto via ON DELETE CASCADE (PRAGMA foreign_keys = ON).
        deleteById: (id) => db.run("DELETE FROM users WHERE id = ?", [id]),
    };
}

module.exports = { createUserModel };

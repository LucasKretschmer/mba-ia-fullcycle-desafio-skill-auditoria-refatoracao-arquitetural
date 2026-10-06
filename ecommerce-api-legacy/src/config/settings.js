const settings = {
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
};

module.exports = settings;

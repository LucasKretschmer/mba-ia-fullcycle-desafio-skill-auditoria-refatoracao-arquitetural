const express = require('express');
const settings = require('./config/settings');
const logger = require('./utils/logger');
const { createDatabase } = require('./database/connection');
const { createModels } = require('./models');
const { createCheckoutService } = require('./services/checkoutService');
const { createReportService } = require('./services/reportService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { buildRoutes } = require('./views/routes');
const { adminOnly } = require('./middlewares/auth');
const { notFound, errorHandler } = require('./middlewares/errorHandler');

function createApp({ db, settings }) {
    const models = createModels(db);
    const checkoutService = createCheckoutService({ db, models });
    const reportService = createReportService({ models });

    const app = express();
    app.use(express.json());
    app.use('/api', buildRoutes({
        checkoutController: createCheckoutController({ checkoutService }),
        reportController: createReportController({ reportService }),
        userController: createUserController({ models }),
        adminOnly: adminOnly(settings),
    }));
    app.use(notFound);
    app.use(errorHandler);
    return app;
}

async function start() {
    const db = await createDatabase(settings.dbPath);
    if (!settings.adminToken) logger.warn('ADMIN_TOKEN não definido: rotas administrativas bloqueadas');

    createApp({ db, settings }).listen(settings.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
}

start().catch((err) => {
    logger.error(`Falha ao iniciar: ${err.stack || err}`);
    process.exit(1);
});

const logger = require('../utils/logger');
const { AppError } = require('../utils/errors');

function notFound(req, res) {
    res.status(404).send('Not Found');
}

// Respostas de erro em texto puro, como a API original.
function errorHandler(err, req, res, next) {
    if (err instanceof AppError) return res.status(err.statusCode).send(err.message);

    const status = err.status || 500;
    if (status >= 500) {
        logger.error(err.stack || String(err));
        return res.status(500).send('Erro interno');
    }
    res.status(status).send('Bad Request');
}

module.exports = { notFound, errorHandler };

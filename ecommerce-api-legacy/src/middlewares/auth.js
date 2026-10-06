const crypto = require('crypto');
const { ForbiddenError } = require('../utils/errors');

function tokensMatch(provided, expected) {
    const a = Buffer.from(provided);
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// Sem ADMIN_TOKEN configurado as rotas administrativas ficam bloqueadas.
function adminOnly(settings) {
    return (req, res, next) => {
        const provided = req.get('X-Admin-Token') || '';
        if (!settings.adminToken || !tokensMatch(provided, settings.adminToken)) {
            return next(new ForbiddenError());
        }
        next();
    };
}

module.exports = { adminOnly };

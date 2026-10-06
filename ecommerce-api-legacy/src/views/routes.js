const express = require('express');

const asyncHandler = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);

function buildRoutes({ checkoutController, reportController, userController, adminOnly }) {
    const router = express.Router();
    router.post('/checkout', asyncHandler(checkoutController.checkout));
    router.get('/admin/financial-report', adminOnly, asyncHandler(reportController.financialReport));
    router.delete('/users/:id', adminOnly, asyncHandler(userController.remove));
    return router;
}

module.exports = { buildRoutes };

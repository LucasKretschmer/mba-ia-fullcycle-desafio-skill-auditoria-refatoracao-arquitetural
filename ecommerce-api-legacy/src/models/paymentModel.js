const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

const authorize = (cardNumber) => (cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED);

function createPaymentModel(db) {
    return {
        authorize,
        create: (enrollmentId, amount, status) => db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]),
    };
}

module.exports = { createPaymentModel };

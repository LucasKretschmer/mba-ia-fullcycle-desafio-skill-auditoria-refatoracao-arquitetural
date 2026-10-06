const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Regra do gateway simulado: só cartões com este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

const COURSE_ACTIVE = 1;

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, COURSE_ACTIVE };

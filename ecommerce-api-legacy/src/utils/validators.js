const { ValidationError } = require('./errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+$/;

const isFilledString = (value) => typeof value === 'string' && value.trim() !== '';

function parseId(value) {
    const id = Number(value);
    if (!Number.isInteger(id) || id <= 0) throw new ValidationError();
    return id;
}

function validateCheckout(body) {
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = body || {};

    if (!isFilledString(name) || !isFilledString(email) || !isFilledString(cardNumber)) {
        throw new ValidationError();
    }
    if (!EMAIL_PATTERN.test(email)) throw new ValidationError();
    if (password !== undefined && password !== null && typeof password !== 'string') {
        throw new ValidationError();
    }

    return {
        name,
        email,
        password: password || null,
        courseId: parseId(courseId),
        cardNumber,
    };
}

module.exports = { validateCheckout, parseId };

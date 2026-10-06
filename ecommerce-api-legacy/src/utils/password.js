const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const hash = await scrypt(password, salt, KEY_LENGTH);
    return `${salt}:${hash.toString('hex')}`;
}

module.exports = { hashPassword };

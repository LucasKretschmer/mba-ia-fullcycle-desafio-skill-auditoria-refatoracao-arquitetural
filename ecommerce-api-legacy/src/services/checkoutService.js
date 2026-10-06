const { PAYMENT_STATUS } = require('../config/constants');
const { NotFoundError, AppError } = require('../utils/errors');
const { hashPassword } = require('../utils/password');
const logger = require('../utils/logger');

function createCheckoutService({ db, models }) {
    const { users, courses, enrollments, payments, auditLogs } = models;

    async function checkout({ name, email, password, courseId, cardNumber }) {
        const course = await courses.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const status = payments.authorize(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

        const passwordHash = password ? await hashPassword(password) : null;

        const enrollmentId = await db.transaction(async () => {
            const existing = await users.findByEmail(email);
            const userId = existing ? existing.id : await users.create(name, email, passwordHash);
            const newEnrollmentId = await enrollments.create(userId, courseId);
            await payments.create(newEnrollmentId, course.price, status);
            await auditLogs.register(`Checkout curso ${courseId} por ${userId}`);
            return newEnrollmentId;
        });

        logger.info(`Checkout aprovado: matrícula ${enrollmentId}, cartão final ${cardNumber.slice(-4)}`);
        return { enrollmentId };
    }

    return { checkout };
}

module.exports = { createCheckoutService };

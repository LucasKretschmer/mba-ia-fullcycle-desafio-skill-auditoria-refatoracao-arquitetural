class AppError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.statusCode = statusCode;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') {
        super(message, 400);
    }
}

class NotFoundError extends AppError {
    constructor(message) {
        super(message, 404);
    }
}

class ForbiddenError extends AppError {
    constructor(message = 'Acesso negado') {
        super(message, 403);
    }
}

module.exports = { AppError, ValidationError, NotFoundError, ForbiddenError };

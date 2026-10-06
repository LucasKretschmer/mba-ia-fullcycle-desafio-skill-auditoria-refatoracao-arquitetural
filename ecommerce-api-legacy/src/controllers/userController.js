const { parseId } = require('../utils/validators');

function createUserController({ models }) {
    return {
        async remove(req, res) {
            await models.users.deleteById(parseId(req.params.id));
            res.send('Usuário deletado');
        },
    };
}

module.exports = { createUserController };

function write(level, output) {
    return (message) => output(`[${new Date().toISOString()}] ${level} ${message}`);
}

module.exports = {
    info: write('INFO', console.log),
    warn: write('WARN', console.warn),
    error: write('ERROR', console.error),
};

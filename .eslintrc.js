module.exports = {
    env: {
        browser: true,
        commonjs: true,
        es2021: true,
        node: true
    },
    extends: 'eslint:recommended',
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
    },
    rules: {
        'complexity': ['warn', 10],
        'max-lines': ['warn', 300],
        'max-lines-per-function': ['warn', 50],
        'max-depth': ['warn', 4],
        'max-params': ['warn', 4],
        'no-console': 'off',
        'no-unused-vars': 'warn',
        'prefer-const': 'warn',
        'no-var': 'error'
    }
};
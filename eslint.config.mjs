import js from '@eslint/js';

export default [
    js.configs.recommended,
    {
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'commonjs',
            globals: {
                console: 'readonly',
                process: 'readonly',
                require: 'readonly',
                module: 'readonly',
                exports: 'readonly',
                __dirname: 'readonly',
                __filename: 'readonly',
                Buffer: 'readonly',
                global: 'readonly',
                setTimeout: 'readonly',
                setInterval: 'readonly',
                clearTimeout: 'readonly',
                clearInterval: 'readonly'
            }
        },
        rules: {
            'complexity': ['warn', 10],
            'max-lines': ['warn', 300],
            'max-depth': ['warn', 4],
            'max-params': ['warn', 4],
            'no-console': 'off',
            'no-unused-vars': 'warn',
            'prefer-const': 'warn',
            'no-var': 'error'
        },
        ignores: ['**/._*', '**/node_modules/**', '**/.tmp/**']
    }
];
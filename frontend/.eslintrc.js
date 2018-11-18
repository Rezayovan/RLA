module.exports = {
    'extends': 'eslint:recommended',
    'parserOptions': {
        'ecmaVersion': 6,
        'sourceType': 'module',
    },
    'env': {
        'browser': true,
        'es6': true,
    },
    'rules': {
        'no-console': 'off',
    },
    'globals': {
        'axios': true,
        'API_ROOT': true,
    }
};

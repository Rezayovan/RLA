module.exports = {
    "extends": "eslint:recommended",
    "parserOptions": {
        "ecmaVersion": 6
    },
    "env": {
        "browser": true,
        "es6": true,
    },
    "rules": {
        "quotes": ["warn", "double"],
        "no-console": "off",
    },
    "globals": {
        "axios": true,
    }
};

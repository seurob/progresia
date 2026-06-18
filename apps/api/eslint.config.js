const js = require("@eslint/js");
const tseslint = require("typescript-eslint");

module.exports = tseslint.config(
  {
    ignores: ["dist", "eslint.config.js", "jest.config.js"]
  },
  js.configs.recommended,
  ...tseslint.configs.recommended
);

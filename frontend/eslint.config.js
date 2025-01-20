import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import js from "@eslint/js";

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    files: ["**/*.{js,mjs,cjs,vue}"],
    ignores: [
      "**/dist/*",
      "./node_modules/**/*",
      '**/dev/*',
      '**/tests/*',
    ]
  },
  {
    ...js.configs.recommended,
    ignores: ["dist/**/*.js"]
  },
  {files: ["**/*.js"], languageOptions: {sourceType: "commonjs"}},
  {languageOptions: { globals: globals.browser }},
  ...pluginVue.configs["flat/essential"]
];
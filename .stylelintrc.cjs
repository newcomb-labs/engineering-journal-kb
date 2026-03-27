module.exports = {
  ignoreFiles: [
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "website/.docusaurus/**",
    "website/build/**",
  ],
  extends: ["stylelint-config-standard"],
  rules: {
    "selector-class-pattern": null,
    "keyframes-name-pattern": null,
  },
};

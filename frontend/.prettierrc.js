module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 120,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  arrowParens: 'always',
  overrides: [
    {
      files: '*.js',
      options: { parser: 'babel' },
    },
    {
      files: '*.ts',
      options: { parser: 'typescript' },
    },
    {
      files: '*.json',
      options: { parser: 'json' },
    },
    {
      files: '*.md',
      options: { parser: 'markdown' },
    },
  ],
};

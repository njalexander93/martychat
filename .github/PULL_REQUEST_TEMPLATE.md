## Summary

<!-- Provide a brief summary of the changes -->

## Related Issues

<!-- Link to issues/tickets (e.g., Closes #123) -->

## Change Type

<!-- Select the type of change using an "x" inside the brackets -->

- [ ] 🆕 Feature
- [ ] 🐛 Bug Fix
- [ ] 🔨 Refactor
- [ ] 📖 Documentation Update
- [ ] 🚀 Performance Improvement
- [ ] ✅ Test Improvement
- [ ] ⚠️ Breaking Change

## How to Test

### Setup the environment variables

```sh
# Copy template files and fill necessary values
cp .env.local.template .env.local
cp frontend/.env.local.template frontend/.env.local
cp backend/.env.local.template backend/.env.local
cp backend/sam/env.json.template backend/sam/env.json
```

### Run the Application Locally

Frontend

```sh
cd frontend
npm run dev
```

Backend

```sh
cd backend
export ENV=development && uvicorn main:app --port 8000 --reload
```

SAM (Local Lambda Environment Simulator)

```sh
cd backend/sam
sam local start-api --env-vars env.json --port 9000
```

### Frontend Testing and Linting

Run Jest Testing

```sh
cd frontend

# Run full test suite
npm test --verbose

# Run a specific test
npm test __test__/path/to/test --verbose

# Run tests with coverage report
npm test test:coverage

# Run tests in watch mode during development
npm run test:watch
```

Run ESLint

```sh
cd frontend

npm run lint

# Fix automatically fixable issues
npm run lint:fix
```

Format code with Prettier

```sh
cd frontend

npm run format
```

### Backend Testing and Linting

Run Pytest

```sh
cd backend

# Run all tests
pytest

# Run a specific test suite
pytest tests/path/to/test/suite

# Run a specific test
pytest tests/path/to/test/suite::test

# Run pytest with a coverage report
pytest --cov=.
```

Run Ruff for Linting and Formatting

```sh
# Check code
ruff check --fix --exit-non-zero-on-fix backend/

# Format code
ruff format --line-length=120 backend/
```

Run Type Checking with mypy

```sh
mypy --ignore-missing-imports backend/
```

## Security Checks

Run npm audit

```sh
npm audit --audit-level=high
```

Run pip-audit

```sh
pip install pip-audit
pip-audit -r backend/requirements.txt --ignore-vuln GHSA-hcpj-qp55-gfph
```

## Screenshots (if applicable)

<!-- Add before/after screenshots -->

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules

## Breaking Changes

<!-- Describe any breaking changes and their impact -->

## Additional Notes

<!-- Any other relevant details -->

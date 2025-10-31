# Changelog

## [Unreleased]

### Security

- **BREAKING CHANGE (Future Release)**: The placeholder SECRET_KEY value "your-secret-key-here" will be rejected in a future release
  - Current behavior: Emits deprecation warning but continues to work
  - Migration: Generate a secure SECRET_KEY with: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
  - Set the generated key in your `.env` file: `SECRET_KEY=your_generated_key_here`

### Fixed

- Fixed SECRET_KEY validation to emit deprecation warnings for placeholder values
- Fixed YOU_API_KEY validation to skip checks in demo mode
- Fixed undefined variable reference in demo recording script
- Fixed scope issues in Python demo recording script
- Fixed deprecated datetime.utcnow() usage in exception handling
- Fixed rate limiter to use Redis backend for distributed deployments
- Fixed WebSocket tests to use real orchestration instead of manual emits
- Fixed test settings initialization to handle validation errors gracefully

### Changed

- Rate limiter now uses Redis storage backend for multi-process deployments
- Exception timestamps now use timezone-aware datetime objects
- Demo mode bypasses YOU_API_KEY validation with warning log

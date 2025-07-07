# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please send an email to onno@brouwerict.com.

Please include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

We will respond within 48 hours and provide a timeline for fixing the issue.

## Known Security Considerations

### Current Status (v1.0.0)

#### Fixed Issues
- **Path Traversal**: Added path sanitization in API endpoints
- **Input Validation**: Implemented directory restrictions for file operations

#### Frontend Dependencies
- **nth-check**: RegExp complexity issue (Medium Impact)
  - Affects: React build tools only
  - Mitigation: Not exposed in production build
  
- **webpack-dev-server**: Information exposure (Medium Impact)
  - Affects: Development environment only
  - Mitigation: Not used in production
  
- **PostCSS**: Input validation issue (Low Impact)
  - Affects: Build process only
  - Mitigation: Not exposed at runtime

#### Recommendations
1. **Production Deployment**: Use built static files, not dev server
2. **File Uploads**: Implement additional file type validation
3. **Authentication**: Add authentication for sensitive API endpoints
4. **Rate Limiting**: Implement API rate limiting
5. **Input Sanitization**: Continue expanding input validation

## Security Best Practices

When using PDF2UBL:
1. Run in isolated environment (Docker recommended)
2. Validate all PDF inputs
3. Monitor file system access
4. Use HTTPS in production
5. Regularly update dependencies

## Development Security

For contributors:
1. Run `npm audit` before submitting PRs
2. Use `bandit` for Python security analysis
3. Follow secure coding practices
4. Test with malicious inputs

## Automated Security

- **CodeQL**: Automated code analysis
- **Trivy**: Vulnerability scanning
- **Dependabot**: Dependency updates
- **GitHub Security**: Continuous monitoring
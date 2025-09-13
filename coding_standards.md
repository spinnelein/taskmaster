# Professional Coding Standards for Claude Code

## CRITICAL RULES - NO EXCEPTIONS

### 1. CHARACTER ENCODING
- **NEVER use emojis anywhere in code** - causes Unicode errors and deployment issues
- **ASCII ONLY** in all code files, comments, variable names, console output
- No Unicode characters except in user-facing content strings when explicitly required

### 2. FILE ORGANIZATION
- **NO monolithic files** - break code into logical, single-responsibility modules
- **Maximum file size for Claude Code compatibility:**
  - Keep files under 1000 lines or 50KB so Claude Code can read entire file into memory
  - Preferred maximum: 200-300 lines per file for readability
  - Large data files (JSON, SQL dumps) should be split or processed in chunks
- Follow established directory conventions for the language/framework
- One class/major function per file when appropriate
- Separate concerns: models, views, controllers, utilities, tests
- If a file grows beyond readable limits, refactor into smaller modules
- **Test and temporary files:**
  - Create temporary files in `/temp/` or `/scratch/` directory
  - Never leave test files in the main codebase
  - Clean up test files when done with experiments

### 3. PROJECT STRUCTURE
- **Always analyze existing project structure first** before creating new files
- Follow the established patterns and conventions
- Maintain consistent directory hierarchy
- Group related functionality together
- Keep configuration separate from business logic

### 4. CODE QUALITY
- Use clear, descriptive variable and function names
- Write self-documenting code
- Add comments only when necessary to explain "why", not "what"
- Follow language-specific naming conventions (camelCase, snake_case, etc.)
- Avoid deeply nested code - refactor into smaller functions

### 5. MAINTAINABILITY
- **Single Responsibility Principle** - each function/class does one thing well
- **DRY (Don't Repeat Yourself)** - extract common code into reusable functions
- Keep functions small and focused (typically 10-30 lines)
- Minimize dependencies between modules
- Use consistent error handling patterns

## LANGUAGE-SPECIFIC STANDARDS

### JavaScript/TypeScript
```
Directory Structure:
/src
  /components  - React components (one per file)
  /hooks      - Custom React hooks
  /utils      - Pure utility functions
  /services   - API calls and external services
  /types      - TypeScript type definitions
  /constants  - Application constants
/tests        - Test files mirroring src structure
/docs         - Documentation
```

### Python
```
Directory Structure:
/src or /app
  /models     - Data models
  /views      - View functions/classes
  /services   - Business logic
  /utils      - Utility functions
  /config     - Configuration files
/tests        - Test files
/docs         - Documentation
requirements.txt - Dependencies
```

### General Backend
```
/controllers  - Request handling
/models       - Data layer
/services     - Business logic
/middleware   - Cross-cutting concerns
/config       - Configuration
/utils        - Shared utilities
```

## FILE NAMING CONVENTIONS
- Use kebab-case for directories: `user-management/`
- Use camelCase for JavaScript files: `userService.js`
- Use snake_case for Python files: `user_service.py`
- Use PascalCase for React components: `UserProfile.jsx`
- Be descriptive: `authenticationService.js` not `auth.js`

## DOCUMENTATION REQUIREMENTS
- Maintain PROJECT_STATUS.md with current milestone and progress
- Update README.md with setup and usage instructions
- Document API endpoints and data structures
- Keep ARCHITECTURE.md explaining overall system design
- Comment complex algorithms or business rules

## BEFORE WRITING ANY CODE
1. **Read existing project structure**
2. **Understand the current architecture**
3. **Check for existing similar functionality**
4. **Plan where new code should go**
5. **Consider how it fits with existing patterns**

## ERROR HANDLING
- Use consistent error handling patterns
- Log errors appropriately
- Provide meaningful error messages
- Handle edge cases explicitly
- Don't fail silently

## PERFORMANCE CONSIDERATIONS
- Avoid unnecessary complexity
- Consider memory usage for large datasets
- Use appropriate data structures
- Don't premature optimize, but don't ignore obvious inefficiencies

## SECURITY BASICS
- Validate all inputs
- Sanitize user data
- Use environment variables for secrets
- Follow framework security best practices
- Don't log sensitive information

## TESTING REQUIREMENTS
- Write tests for new functionality
- Maintain existing test coverage
- Use descriptive test names
- Test edge cases and error conditions

## COMMIT STANDARDS
- Write clear, descriptive commit messages
- Commit logical units of work
- Don't commit commented-out code
- Don't commit debugging statements or console.logs

---

## ENFORCEMENT REMINDERS

**Every Claude Code session should start with:**
"Follow CODING_STANDARDS.md strictly. No emojis, no monolithic files, analyze existing structure first."

**If Claude Code violates these standards:**
"STOP. Review CODING_STANDARDS.md. Refactor this code to follow professional standards."

**For large features:**
"Break this into multiple files following the directory structure in CODING_STANDARDS.md."
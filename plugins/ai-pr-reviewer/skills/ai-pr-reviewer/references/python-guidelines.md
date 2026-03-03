# Python Code Review Guidelines for AI Reviewers

> **Target:** Python 3.11+ | **Audience:** Junior to Architect | **Scope:** Web APIs (FastAPI/Django/Flask), CLI Tools, Data Pipelines, Libraries, Microservices

This document provides comprehensive guidelines for AI-powered code review of Python projects. Only negative issues should be reported using the severity classification below.

---

## Severity Classification

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| **🔴 Critical** | Security vulnerabilities, data loss risks, production crashes, blocking bugs | Must fix before merge |
| **🟠 Major** | Performance issues, code correctness problems, maintainability concerns, significant best practice violations | Should fix before merge |
| **🟡 Minor** | Code style issues, minor optimizations, documentation gaps, suggestions for improvement | Can fix in follow-up PR |

---

## Table of Contents

1. [Security Review](#1-security-review)
2. [Performance Review](#2-performance-review)
3. [Code Correctness](#3-code-correctness)
4. [Architecture & Design](#4-architecture--design)
5. [Clean Architecture & Domain-Driven Design](#5-clean-architecture--domain-driven-design)
6. [API Design](#6-api-design)
7. [Data Access](#7-data-access)
8. [Validation Patterns](#8-validation-patterns)
9. [Configuration Management](#9-configuration-management)
10. [Middleware & Pipeline](#10-middleware--pipeline)
11. [Background Tasks & Workers](#11-background-tasks--workers)
12. [Resiliency Patterns](#12-resiliency-patterns)
13. [Serialization & Data Formats](#13-serialization--data-formats)
14. [Messaging Patterns](#14-messaging-patterns)
15. [Feature Management](#15-feature-management)
16. [Dependency Management](#16-dependency-management)
17. [Testing](#17-testing)
18. [Logging & Observability](#18-logging--observability)
19. [Project & Code Structure](#19-project--code-structure)
20. [Anti-Patterns to Flag](#20-anti-patterns-to-flag)
21. [Naming & Style](#21-naming--style-pep-8-conventions)
22. [Modern Python 3.11+ Features](#22-modern-python-311-features)

---

## 1. Security Review

### 1.1 Critical Security Issues

#### **[SEC-1]** SQL Injection
- **Flag:** String concatenation or f-strings in SQL queries
- **Flag:** `%` formatting or `.format()` in raw SQL statements
- **Flag:** `cursor.execute(f"SELECT ... WHERE id = {user_id}")`
- **Expect:** Parameterized queries (`cursor.execute("SELECT ... WHERE id = %s", (user_id,))`)
- **Expect:** ORM query builders (SQLAlchemy, Django ORM)

#### **[SEC-2]** Command Injection
- **Flag:** `os.system()` with user-controlled input
- **Flag:** `subprocess.call(shell=True)` with unsanitized input
- **Flag:** `eval()`, `exec()`, `compile()` with user-controlled data
- **Flag:** `__import__()` with dynamic user input
- **Expect:** `subprocess.run()` with argument lists (no `shell=True`), `shlex.quote()` when shell is required

#### **[SEC-3]** Authentication & Authorization
- **Flag:** Missing authentication on sensitive endpoints
- **Flag:** Hardcoded credentials, API keys, or connection strings in source code
- **Flag:** Weak password hashing (MD5, SHA1, plain text)
- **Flag:** JWT tokens without expiration or signature verification
- **Flag:** Missing CSRF protection on state-changing endpoints
- **Flag:** Overly permissive `@login_not_required` or public decorators
- **Expect:** `bcrypt`/`argon2` for password hashing, secrets in environment/vault, proper token validation

#### **[SEC-4]** Sensitive Data Exposure
- **Flag:** Logging sensitive data (passwords, tokens, PII)
- **Flag:** Returning sensitive fields in API responses unnecessarily
- **Flag:** Storing sensitive data in plain text (files, databases)
- **Flag:** Sensitive data in query strings or URLs
- **Flag:** Secrets committed in `.env` files or config files in source control
- **Expect:** Data masking, encryption at rest, minimal data exposure, `.env` in `.gitignore`

#### **[SEC-5]** Insecure Deserialization
- **Flag:** `pickle.loads()` on untrusted data
- **Flag:** `yaml.load()` without `Loader=yaml.SafeLoader`
- **Flag:** `marshal.loads()` on untrusted input
- **Flag:** `shelve` with untrusted data
- **Expect:** `json.loads()` for untrusted data, `yaml.safe_load()`, validated deserialization

#### **[SEC-6]** Path Traversal
- **Flag:** User input in file paths without validation (`open(user_input)`)
- **Flag:** Missing `os.path.abspath()` or `pathlib.Path.resolve()` validation
- **Flag:** `..` sequences not stripped from file paths
- **Expect:** `pathlib.Path.resolve()` with base directory validation, `os.path.commonpath()` checks

#### **[SEC-7]** CORS Misconfiguration
- **Flag:** `allow_origins=["*"]` combined with `allow_credentials=True`
- **Flag:** Wildcard origins in production configurations
- **Expect:** Explicit origin whitelist, environment-specific CORS settings

#### **[SEC-8]** Server-Side Request Forgery (SSRF)
- **Flag:** User-controlled URLs passed directly to `requests.get()` or `httpx.get()`
- **Flag:** Missing URL scheme validation (allowing `file://`, `ftp://`)
- **Flag:** No internal network address blocking
- **Expect:** URL allowlist, scheme validation, private IP range blocking

### 1.2 Major Security Issues

#### **[SEC-9]** Cryptography
- **Flag:** MD5, SHA1 for security purposes (acceptable for checksums)
- **Flag:** `random` module for security-sensitive operations
- **Flag:** Hardcoded encryption keys or initialization vectors
- **Flag:** Custom cryptography implementations
- **Expect:** `hashlib.sha256()`+, `secrets` module, keys from secure storage, `cryptography` library

#### **[SEC-10]** Input Validation
- **Flag:** Missing validation on API inputs
- **Flag:** Unbounded input sizes (large file uploads, long strings)
- **Flag:** Missing Content-Type validation
- **Flag:** Regular expressions vulnerable to ReDoS
- **Expect:** Pydantic models, Django forms, marshmallow schemas, input size limits

#### **[SEC-11]** HTTP Security Headers
- **Flag:** Missing security headers (HSTS, X-Content-Type-Options, X-Frame-Options)
- **Flag:** `DEBUG = True` in production Django settings
- **Flag:** Missing `SECRET_KEY` rotation strategy
- **Expect:** Security middleware configured, production-safe settings

#### **[SEC-12]** Template Injection
- **Flag:** `Jinja2` templates with `autoescape=False` and user input
- **Flag:** Server-Side Template Injection (SSTI) via user-controlled template strings
- **Flag:** `render_template_string()` with user input in Flask
- **Expect:** Autoescape enabled, user input never used as template source

---

## 2. Performance Review

### 2.1 Critical Performance Issues

#### **[PERF-1]** Async/Await Anti-Patterns
- **Flag:** Blocking calls (`time.sleep()`, synchronous I/O) inside `async` functions
- **Flag:** `requests` library used in async code (use `httpx` or `aiohttp`)
- **Flag:** Synchronous database drivers in async frameworks
- **Flag:** `asyncio.run()` nested inside an already running event loop
- **Flag:** Missing `await` on coroutines (coroutine never executed)
- **Expect:** Proper async libraries (`httpx`, `aiohttp`, `asyncpg`), `asyncio.to_thread()` for CPU-bound work

#### **[PERF-2]** Memory Leaks & Resource Management
- **Flag:** File handles not closed (missing `with` statement)
- **Flag:** Database connections not returned to pool
- **Flag:** Unbounded caches or memoization without size limits
- **Flag:** Large objects held in global/module-level state
- **Flag:** Circular references preventing garbage collection
- **Expect:** Context managers (`with`/`async with`), connection pooling, `functools.lru_cache(maxsize=...)`

#### **[PERF-3]** N+1 Query Problems
- **Flag:** ORM queries inside loops
- **Flag:** Missing `select_related()`/`prefetch_related()` in Django
- **Flag:** Missing eager loading (`.options(joinedload(...))`) in SQLAlchemy
- **Flag:** Lazy loading triggering unexpected queries
- **Expect:** Eager loading, batch queries, `bulk_create()`/`bulk_update()`

### 2.2 Major Performance Issues

#### **[PERF-4]** Collection & Iteration Operations
- **Flag:** Nested loops with O(n²) complexity when O(n) is possible
- **Flag:** `list.append()` in loop when generator expression suffices
- **Flag:** Multiple passes over data when single pass is possible
- **Flag:** Using `list` when `set` or `dict` lookup is needed (O(n) vs O(1))
- **Flag:** `len(list) > 0` instead of truthiness check (`if list:`)
- **Flag:** Creating intermediate lists unnecessarily (use generators)
- **Expect:** Appropriate data structures, generators for large datasets, single-pass algorithms

#### **[PERF-5]** String Operations
- **Flag:** String concatenation in loops (`+=` on strings)
- **Flag:** Repeated string formatting in hot paths
- **Flag:** Not using `str.join()` for building strings from iterables
- **Expect:** `str.join()`, f-strings for formatting, `io.StringIO` for large concatenations

#### **[PERF-6]** Import & Module Loading
- **Flag:** Heavy imports at module level that delay startup
- **Flag:** Importing entire modules when specific names suffice
- **Flag:** Circular imports causing delayed initialization
- **Expect:** Lazy imports for heavy modules, specific imports, clean module hierarchy

#### **[PERF-7]** Database Performance
- **Flag:** Missing database indexes hinted by query patterns
- **Flag:** Loading entire rows when only specific columns needed
- **Flag:** Unbounded queries without pagination or `LIMIT`
- **Flag:** `SELECT *` instead of specific column selection
- **Flag:** Missing connection pooling configuration
- **Expect:** Column projections, pagination, proper indexing, connection pooling

#### **[PERF-8]** Caching
- **Flag:** Expensive computations repeated without caching
- **Flag:** Cache keys that could collide
- **Flag:** Missing cache invalidation strategy
- **Flag:** `@lru_cache` on methods with `self` (caches per instance reference)
- **Expect:** `functools.lru_cache`/`functools.cache`, Redis/Memcached for distributed caching, proper TTL

### 2.3 Minor Performance Issues

- **Flag:** Using `type()` for type checking instead of `isinstance()`
- **Flag:** Regex compilation inside loops (use `re.compile()` at module level)
- **Flag:** Unnecessary list comprehension when generator expression works (`sum([x for x in ...])` → `sum(x for x in ...)`)
- **Flag:** Using `dict.keys()` for membership test instead of direct `in dict`
- **Flag:** `sorted()` when only min/max needed (`min()`/`max()`)
- **Expect:** Compiled regex, generators, appropriate built-in functions

---

## 3. Code Correctness

### 3.1 Critical Correctness Issues

#### **[CORR-1]** Mutable Default Arguments
- **Flag:** Mutable default arguments (`def func(items=[])`, `def func(data={})`)
- **Flag:** Default argument objects shared across calls
- **Expect:** `None` as default with `if items is None: items = []`

#### **[CORR-2]** Exception Handling
- **Flag:** Bare `except:` clauses (catches `SystemExit`, `KeyboardInterrupt`)
- **Flag:** `except Exception` without logging or re-raising
- **Flag:** Empty `except` blocks (swallowing exceptions silently)
- **Flag:** `except` with broad types catching unrelated errors
- **Flag:** Exception handling that alters control flow incorrectly
- **Expect:** Specific exception types, proper logging, `raise` to re-raise, `except Exception as e`

#### **[CORR-3]** Thread Safety
- **Flag:** Shared mutable state without locks in threaded code
- **Flag:** GIL reliance for atomicity in multi-process scenarios
- **Flag:** Race conditions in singleton/module-level initialization
- **Flag:** Non-thread-safe operations on shared containers
- **Expect:** `threading.Lock`, `queue.Queue`, `concurrent.futures`, immutable shared state

#### **[CORR-4]** Resource Management
- **Flag:** File handles, sockets, database connections not properly closed
- **Flag:** Missing `with` statement for context managers
- **Flag:** `__del__` relied upon for cleanup (non-deterministic)
- **Flag:** Missing `finally` blocks for critical cleanup
- **Expect:** Context managers (`with`), `contextlib.closing()`, `atexit` for global cleanup

#### **[CORR-5]** Type Safety
- **Flag:** Ignoring type checker errors (`type: ignore` without justification)
- **Flag:** `Any` type used excessively, hiding type information
- **Flag:** Missing return type annotations on public functions
- **Flag:** `Optional` types not checked before access
- **Expect:** Full type annotations, `mypy`/`pyright` compliance, proper `Optional` handling

### 3.2 Major Correctness Issues

#### **[CORR-6]** Equality and Comparison
- **Flag:** `is` used for value comparison (except `None`, `True`, `False`)
- **Flag:** `==` used for `None` comparison (use `is None`)
- **Flag:** Missing `__eq__` and `__hash__` consistency
- **Flag:** Comparing floats with `==` (use `math.isclose()`)
- **Expect:** `==` for values, `is` for identity, `@dataclass` or `__eq__`/`__hash__` pairs

#### **[CORR-7]** Async Correctness
- **Flag:** Missing `await` on coroutine calls
- **Flag:** Fire-and-forget tasks without exception handling
- **Flag:** `asyncio.gather()` without `return_exceptions=True` when needed
- **Flag:** Missing cancellation handling in long-running async tasks
- **Expect:** Proper `await`, task groups (Python 3.11+), cancellation support

#### **[CORR-8]** Date/Time Handling
- **Flag:** Naive `datetime` used for cross-timezone operations
- **Flag:** `datetime.now()` instead of `datetime.now(tz=timezone.utc)` for UTC
- **Flag:** Timezone assumptions in string parsing
- **Flag:** Incorrect DST handling
- **Expect:** `datetime.now(tz=timezone.utc)`, `zoneinfo.ZoneInfo`, aware datetimes, ISO 8601 formatting

#### **[CORR-9]** Iterator & Generator Issues
- **Flag:** Iterating over a consumed iterator/generator a second time
- **Flag:** Modifying a collection while iterating over it
- **Flag:** `StopIteration` leaking out of generators (Python 3.7+ RuntimeError)
- **Expect:** Materializing iterators when reuse needed, copy before mutation

---

## 4. Architecture & Design

### 4.1 Critical Architecture Issues

#### **[ARCH-1]** Dependency Injection & Inversion
- **Flag:** Hard-coded dependencies (`import`-level coupling to concrete implementations)
- **Flag:** Service Locator pattern (global registries accessed inside business logic)
- **Flag:** Circular imports indicating circular dependencies
- **Flag:** Business logic directly instantiating infrastructure (e.g., `requests.get()` in domain code)
- **Expect:** Constructor/function parameter injection, dependency-injection frameworks (`dependency-injector`, FastAPI `Depends()`)

#### **[ARCH-2]** Layer Violations
- **Flag:** Domain/business logic importing infrastructure modules (HTTP clients, ORM, file I/O)
- **Flag:** Route handlers containing business logic
- **Flag:** Data access code in presentation layer
- **Flag:** Cross-cutting concerns scattered instead of centralized
- **Expect:** Clean layer boundaries, proper separation of concerns

### 4.2 Major Architecture Issues

#### **[ARCH-3]** SOLID Principles
- **Flag:** Classes/modules with multiple responsibilities (SRP violation)
- **Flag:** God classes/modules exceeding reasonable size (>500 lines typically)
- **Flag:** Tight coupling to concrete implementations (DIP violation)
- **Flag:** Fat interfaces/abstract classes (ISP violation)
- **Expect:** Small focused modules, dependency on abstractions (Protocols/ABCs)

#### **[ARCH-4]** Design Patterns
- **Flag:** Incorrect pattern implementation
- **Flag:** Over-engineering simple solutions
- **Flag:** Missing appropriate patterns (e.g., Strategy for complex conditionals)
- **Flag:** Reinventing standard library functionality
- **Expect:** Appropriate pattern usage, Pythonic idioms, KISS principle

---

## 5. Clean Architecture & Domain-Driven Design

### 5.1 Layer Responsibilities

#### **[CLEAN-1]** Domain Layer (Core/Entities)
**Purpose:** Contains enterprise business rules, entities, value objects, domain events, and domain services.

##### Critical Issues
- **Flag:** Infrastructure imports (`sqlalchemy`, `django.db`, `requests`, `httpx`, `boto3`)
- **Flag:** Framework dependencies (FastAPI, Flask, Django specifics)
- **Flag:** ORM model annotations or base classes in pure domain entities
- **Flag:** References to Application, Infrastructure, or Presentation layers
- **Expect:** Pure Python with no external dependencies, self-contained business logic

##### Major Issues
- **Flag:** Anemic entities (only data attributes, no behavior)
- **Flag:** Public mutable attributes without invariant protection
- **Flag:** Missing domain validation in entity constructors
- **Flag:** Primitive obsession (using `str`, `int` instead of value objects)
- **Flag:** Domain events not raised for significant state changes
- **Expect:** Rich domain models with `@dataclass`/`@attrs`, value objects, encapsulated state

##### Entity Guidelines
- **Flag:** Entities without identity
- **Flag:** Mutable value objects (value objects should be frozen dataclasses)
- **Flag:** Direct mutable collection exposure (`list` attribute without defensive copy)
- **Flag:** Business rules in services that belong in entities
- **Expect:** `@dataclass(frozen=True)` for value objects, factory methods, domain methods for state changes

##### Aggregate Guidelines
- **Flag:** Aggregates too large (performance issues)
- **Flag:** References between aggregates by object instead of ID
- **Flag:** Missing aggregate root validation
- **Flag:** Child entities accessible without going through aggregate root
- **Expect:** Small aggregates, ID references, root controls children

#### **[CLEAN-2]** Application Layer (Use Cases)
**Purpose:** Contains application business rules, use cases, command/query handlers, DTOs, and interfaces for infrastructure.

##### Critical Issues
- **Flag:** Direct infrastructure implementations (database queries, HTTP calls)
- **Flag:** Domain entities returned directly to presentation layer
- **Flag:** References to Presentation or Infrastructure layers
- **Expect:** Depends only on Domain layer, defines interfaces (Protocols/ABCs) implemented by Infrastructure

##### Major Issues
- **Flag:** Business logic that belongs in Domain layer
- **Flag:** Missing command/query separation (when using CQRS)
- **Flag:** Services doing too much (violating SRP)
- **Flag:** Missing input validation before domain operations
- **Flag:** Transaction management logic scattered across handlers
- **Expect:** Orchestration logic only, thin handlers, clear use cases

##### Interface Definitions
- **Flag:** Infrastructure-specific types in Protocol/ABC definitions
- **Flag:** Overly broad interfaces (interface segregation violation)
- **Flag:** Missing async methods for I/O operations
- **Expect:** Clean abstractions, specific Protocols, async by default for I/O

##### DTO Guidelines
- **Flag:** DTOs with behavior (methods other than simple transforms)
- **Flag:** Domain entities used as DTOs
- **Flag:** DTOs exposing internal IDs unnecessarily
- **Flag:** Missing mapping functions between domain and DTOs
- **Expect:** Pydantic models or `@dataclass` for DTOs, explicit mapping functions

#### **[CLEAN-3]** Infrastructure Layer
**Purpose:** Contains implementations of interfaces defined in Application layer, external service integrations, database access.

##### Critical Issues
- **Flag:** Business logic in infrastructure implementations
- **Flag:** Domain layer importing infrastructure types
- **Flag:** Infrastructure types exposed through Application interfaces
- **Expect:** Implements Application layer Protocols/ABCs, contains only technical concerns

##### Major Issues
- **Flag:** Repository methods with business logic
- **Flag:** Missing unit of work pattern for transactions
- **Flag:** Direct ORM session injection in Application layer
- **Flag:** External service calls without abstraction
- **Expect:** Pure data access, proper abstractions, isolated external dependencies

##### Repository Guidelines
- **Flag:** Generic repository hiding ORM capabilities
- **Flag:** Repository returning raw ORM query objects (leaky abstraction)
- **Flag:** Missing specification pattern for complex queries
- **Expect:** Specific repositories, materialized returns, CQRS for complex reads

#### **[CLEAN-4]** Presentation Layer (API/Web)
**Purpose:** Contains route handlers, view models, API endpoints, middleware, and dependency wiring.

##### Critical Issues
- **Flag:** Business logic in route handlers/views
- **Flag:** Direct domain entity manipulation in views
- **Flag:** Infrastructure dependencies (raw DB sessions) in handlers
- **Expect:** Thin handlers, delegates to Application layer use cases

##### Major Issues
- **Flag:** Missing input validation on request models
- **Flag:** Domain exceptions not mapped to HTTP responses
- **Flag:** Inconsistent response formats
- **Flag:** Missing API versioning
- **Expect:** Request validation, exception handlers, consistent response structure

### 5.2 Layer Dependency Rules

```
Presentation
   ↓
Infrastructure
   ↓
Application
   ↓
Domain
```

##### Dependency Violations to Flag
| From | To | Severity |
|------|-----|----------|
| Domain | Application | **Critical** |
| Domain | Infrastructure | **Critical** |
| Domain | Presentation | **Critical** |
| Application | Infrastructure | **Critical** |
| Application | Presentation | **Critical** |
| Infrastructure | Presentation | **Major** |

##### Allowed Dependencies
- Presentation → Infrastructure (DI wiring only) ✓
- Presentation → Application (via use cases) ✓
- Infrastructure → Application (Protocol/ABC implementation) ✓
- Infrastructure → Domain (via Application) ✓
- Application → Domain ✓

### 5.3 CQRS Pattern (when applicable)

#### **[CLEAN-5]** Command Guidelines
- **Flag:** Commands returning data (should return void/ID/Result)
- **Flag:** Commands with query-like names
- **Flag:** Multiple commands in single handler
- **Flag:** Missing command validation
- **Expect:** Clear naming, single responsibility, validation pipeline

#### **[CLEAN-6]** Query Guidelines
- **Flag:** Queries modifying state
- **Flag:** Queries going through domain layer unnecessarily
- **Flag:** Missing pagination on collection queries
- **Expect:** Direct data access for reads, projections, read-optimized models

#### **[CLEAN-7]** Handler Guidelines
- **Flag:** Handlers with mixed read/write operations
- **Flag:** Complex orchestration in handlers (move to domain services)
- **Flag:** Missing cross-cutting concerns (logging, validation)
- **Expect:** Single responsibility, middleware/decorators for cross-cutting

### 5.4 Domain Events

- **Flag:** Domain events raised outside aggregate methods
- **Flag:** Missing event handlers for published events
- **Flag:** Side effects in event raise (should be handled by handlers)
- **Flag:** Events containing entire entities instead of IDs/minimal data
- **Expect:** Events raised in domain, handled in application/infrastructure

---

## 6. API Design

### 6.1 Critical API Issues

#### **[API-1]** REST Conventions (FastAPI / Flask / Django REST Framework)
- **Flag:** GET endpoints modifying state
- **Flag:** Non-idempotent PUT operations
- **Flag:** Missing HTTP status codes for error cases
- **Flag:** Exposing internal exceptions/tracebacks in responses
- **Expect:** Proper HTTP verbs, structured error responses (RFC 7807 Problem Details)

#### **[API-2]** Error Handling
- **Flag:** Inconsistent error response format across endpoints
- **Flag:** Stack traces in production error responses
- **Flag:** Generic 500 errors without logging
- **Flag:** Missing error handling for common cases (404, 422, 409)
- **Expect:** Global exception handlers, structured error responses, proper status codes

### 6.2 Major API Issues

#### **[API-3]** Versioning
- **Flag:** Breaking changes without version bump
- **Flag:** Missing API versioning strategy
- **Expect:** URL prefix (`/api/v1/`) or header-based versioning, backward compatibility

#### **[API-4]** Request/Response Design
- **Flag:** Overly large request/response objects
- **Flag:** Missing pagination on collection endpoints
- **Flag:** Circular references in serialization
- **Flag:** Exposing internal database IDs unnecessarily
- **Flag:** Missing rate limiting on public endpoints
- **Expect:** Pydantic response models, pagination, proper serialization

#### **[API-5]** Documentation
- **Flag:** Missing docstrings on public API endpoints
- **Flag:** OpenAPI/Swagger spec not reflecting actual behavior
- **Flag:** Missing request/response examples
- **Flag:** Undocumented query parameters or headers
- **Expect:** Docstrings, accurate OpenAPI spec, example values

### 6.3 Minor API Issues

- **Flag:** Inconsistent naming conventions in endpoints (mixing snake_case and kebab-case)
- **Flag:** Missing response model declarations in FastAPI
- **Flag:** Hardcoded URL paths (use `url_for()` or route names)
- **Expect:** Consistent URL naming, explicit response models, named routes

---

## 7. Data Access

### 7.1 SQLAlchemy

#### **[DA-1]** Critical Issues
- **Flag:** Sessions not properly closed or committed
- **Flag:** Transactions not used for multi-entity operations
- **Flag:** `session.commit()` inside loops
- **Flag:** Synchronous engine used in async context
- **Expect:** Context-managed sessions, batch operations, `AsyncSession` for async code

#### **[DA-2]** Major Issues
- **Flag:** Business logic in repository/data access layer
- **Flag:** Missing eager loading causing N+1 queries
- **Flag:** `session.query()` (legacy API) in new code (use `select()` 2.0 style)
- **Flag:** Missing `expire_on_commit=False` for detached object access
- **Flag:** Raw SQL without parameterization
- **Expect:** SQLAlchemy 2.0 style queries, proper loading strategies, parameterized raw SQL

#### **[DA-3]** Minor Issues
- **Flag:** Missing index configuration for frequently queried columns
- **Flag:** Implicit column types in model definitions
- **Expect:** Explicit types, proper indexing, migration scripts

### 7.2 Django ORM

#### **[DA-4]** Critical Issues
- **Flag:** Raw SQL with string formatting (`raw(f"SELECT ... {user_input}")`)
- **Flag:** Missing `atomic()` for multi-model operations
- **Flag:** Synchronous ORM calls in async views without `sync_to_async`
- **Expect:** Parameterized raw queries, `transaction.atomic()`, `sync_to_async` wrappers

#### **[DA-5]** Major Issues
- **Flag:** Missing `select_related()`/`prefetch_related()` causing N+1
- **Flag:** `Model.objects.all()` without pagination or limiting
- **Flag:** Signals with heavy side effects
- **Flag:** Fat models with hundreds of lines
- **Expect:** Optimized querysets, pagination, lean models, explicit queries

### 7.3 Alembic / Django Migrations

#### **[DA-6]** Major Issues
- **Flag:** Data migrations mixed with schema migrations
- **Flag:** Missing migration for model changes
- **Flag:** Irreversible migrations without downgrade path
- **Flag:** Migrations with hardcoded data
- **Expect:** Separate data/schema migrations, reversible operations, generated migration files

---

## 8. Validation Patterns

### 8.1 Critical Issues

- **Flag:** Missing validation on untrusted input
- **Flag:** Client-side only validation (no server-side)
- **Flag:** Validation bypassed by direct model construction
- **Expect:** Server-side validation always, defense in depth

### 8.2 Pydantic (FastAPI)

#### **[VAL-1]** Major Issues
- **Flag:** Using `dict` instead of Pydantic models for request/response
- **Flag:** Missing field validators for business constraints
- **Flag:** `model_config` with `extra = "allow"` without justification
- **Flag:** Overly permissive `Any` types in models
- **Flag:** Missing `Field(...)` constraints (min_length, ge, le, pattern)
- **Expect:** Strict Pydantic models, field constraints, custom validators

#### **[VAL-2]** Minor Issues
- **Flag:** Duplicate validation rules across models
- **Flag:** Missing custom error messages on validators
- **Flag:** V1 syntax (`@validator`) in new code (use V2 `@field_validator`)
- **Expect:** Shared validators via mixins, clear error messages, Pydantic V2 syntax

### 8.3 Django Forms / Serializers

#### **[VAL-3]** Major Issues
- **Flag:** Missing `clean_*` methods for field-level validation
- **Flag:** Serializer fields without constraints
- **Flag:** `ModelSerializer` exposing all fields (`fields = "__all__"`)
- **Flag:** Missing `validate()` for cross-field validation
- **Expect:** Explicit field lists, proper validation methods, constrained fields

### 8.4 Domain Validation

#### **[VAL-4]** Major Issues
- **Flag:** Domain invariants not enforced in constructors
- **Flag:** Validation exceptions used for control flow
- **Flag:** Validation scattered across application layer
- **Expect:** Guard clauses, Result/Either pattern, centralized domain validation

---

## 9. Configuration Management

### 9.1 Critical Issues

- **Flag:** Secrets in source code or committed config files
- **Flag:** Production credentials in `.env` files checked into version control
- **Flag:** `DEBUG = True` or equivalent in production settings
- **Flag:** Missing configuration validation at startup
- **Expect:** Environment variables, secret managers (AWS Secrets Manager, HashiCorp Vault), `.env` in `.gitignore`

### 9.2 Settings Patterns

#### **[CONFIG-1]** Major Issues
- **Flag:** Scattered `os.environ.get()` calls throughout codebase
- **Flag:** Missing default values for optional settings
- **Flag:** No centralized settings module/class
- **Flag:** Settings accessed as raw strings without type conversion
- **Flag:** Missing required setting validation at startup
- **Expect:** Pydantic `BaseSettings`, `django-environ`, centralized settings with validation

#### **[CONFIG-2]** Minor Issues
- **Flag:** Settings not organized by feature/concern
- **Flag:** Missing documentation for environment variables
- **Flag:** Inconsistent naming for environment variables
- **Expect:** Prefixed env vars, organized settings, documented configuration

### 9.3 Environment-Specific Configuration

#### **[CONFIG-3]** Major Issues
- **Flag:** Environment checks scattered in code (`if os.environ.get("ENV") == "prod"`)
- **Flag:** Missing environment-specific configuration files
- **Flag:** Hardcoded environment names throughout codebase
- **Expect:** Configuration-driven behavior, environment abstraction, feature flags over env checks

---

## 10. Middleware & Pipeline

### 10.1 Critical Issues

- **Flag:** Exception handling middleware not wrapping all routes
- **Flag:** Authentication middleware order incorrect
- **Flag:** Request body consumed multiple times without buffering
- **Flag:** Middleware exceptions not handled (crashing entire request)
- **Expect:** Correct middleware order, proper error handling in middleware

### 10.2 Major Issues

- **Flag:** Business logic in middleware (use service layer)
- **Flag:** Missing `await call_next(request)` in ASGI middleware (breaks pipeline)
- **Flag:** Long-running synchronous operations in middleware blocking event loop
- **Flag:** Middleware modifying request/response without documentation
- **Expect:** Infrastructure concerns only, proper async, clear documentation

### 10.3 Minor Issues

- **Flag:** Duplicate middleware functionality
- **Flag:** Missing middleware documentation
- **Expect:** Single responsibility, clear purpose per middleware

### 10.4 FastAPI/Starlette Middleware Order

```
1. CORS middleware
2. Trusted Host middleware
3. Exception handling middleware
4. Authentication middleware
5. Request logging/tracing middleware
6. Custom middleware
7. Route handlers
```

### 10.5 Django Middleware Order

```
1. SecurityMiddleware
2. SessionMiddleware
3. CommonMiddleware
4. CsrfViewMiddleware
5. AuthenticationMiddleware
6. MessageMiddleware
7. Custom middleware
```

---

## 11. Background Tasks & Workers

### 11.1 Critical Issues

- **Flag:** Unhandled exceptions killing worker processes
- **Flag:** Missing task idempotency for retried tasks
- **Flag:** Background tasks accessing request-scoped objects after response sent
- **Flag:** Missing graceful shutdown/signal handling
- **Expect:** Try-except in task bodies, idempotent task design, proper scoping

### 11.2 Celery

#### **[BG-1]** Critical Issues
- **Flag:** Tasks without `acks_late=True` for critical operations
- **Flag:** Missing dead-letter queue for failed tasks
- **Flag:** Sensitive data in task arguments (visible in broker)
- **Flag:** Missing `max_retries` on retryable tasks
- **Expect:** Acknowledged after completion, DLQ, data protection, retry limits

#### **[BG-2]** Major Issues
- **Flag:** Long-running tasks without heartbeat/timeout
- **Flag:** Missing `bind=True` for tasks that need `self.retry()`
- **Flag:** Hardcoded retry delays (use exponential backoff)
- **Flag:** Task results stored indefinitely (missing `result_expires`)
- **Flag:** Database operations without proper connection management
- **Expect:** Timeouts, exponential backoff, result expiry, connection pooling

### 11.3 AsyncIO Background Tasks

#### **[BG-3]** Major Issues
- **Flag:** `asyncio.create_task()` without storing reference (task may be GC'd)
- **Flag:** Background tasks without cancellation handling
- **Flag:** Missing `TaskGroup` for structured concurrency (Python 3.11+)
- **Flag:** Unhandled exceptions in background tasks
- **Expect:** Task references stored, cancellation support, structured concurrency

### 11.4 APScheduler / Cron Jobs

#### **[BG-4]** Major Issues
- **Flag:** Scheduled jobs without error handling
- **Flag:** Jobs that can overlap without protection
- **Flag:** Missing job persistence for crash recovery
- **Expect:** Error handling, misfire grace time, persistent job stores

---

## 12. Resiliency Patterns

### 12.1 Critical Issues

- **Flag:** External calls without timeout
- **Flag:** Missing circuit breaker for unreliable external dependencies
- **Flag:** Retry on non-idempotent operations
- **Flag:** No fallback strategy for critical dependencies
- **Expect:** Timeouts on all external calls, circuit breakers, idempotency awareness

### 12.2 Retry Patterns

#### **[RES-1]** Major Issues
- **Flag:** Hardcoded retry counts and delays
- **Flag:** Retrying on all exceptions (should be selective)
- **Flag:** Missing jitter in retry delays (thundering herd)
- **Flag:** Linear backoff instead of exponential
- **Expect:** `tenacity` library, exponential backoff with jitter, specific exception filtering

#### **[RES-2]** Minor Issues
- **Flag:** Retry policies not configurable
- **Flag:** Missing retry documentation
- **Expect:** Configurable retry parameters, clear retry strategy documentation

### 12.3 HTTP Client Resiliency

#### **[RES-3]** Major Issues
- **Flag:** `requests.get()` without `timeout` parameter
- **Flag:** Missing connection pooling (`requests.Session()` or `httpx.Client()`)
- **Flag:** No retry logic for transient HTTP errors (429, 502, 503, 504)
- **Flag:** Missing circuit breaker for external APIs
- **Expect:** Timeouts, session reuse, retry on transient errors, `httpx` with async support

---

## 13. Serialization & Data Formats

### 13.1 Critical Issues

- **Flag:** `pickle` used with untrusted data (arbitrary code execution)
- **Flag:** `yaml.load()` without `SafeLoader` (arbitrary code execution)
- **Flag:** Deserializing untrusted input without schema validation
- **Expect:** Safe deserialization, schema validation, `json` for untrusted data

### 13.2 JSON Serialization

#### **[SER-1]** Major Issues
- **Flag:** Manual `json.dumps()`/`json.loads()` when Pydantic available
- **Flag:** Missing error handling on deserialization
- **Flag:** Custom JSON encoders without documentation
- **Flag:** `datetime` serialized inconsistently (not ISO 8601)
- **Expect:** Pydantic models for serialization, ISO 8601 dates, error handling

#### **[SER-2]** Minor Issues
- **Flag:** `ensure_ascii=True` when UTF-8 output is appropriate
- **Flag:** Missing `default` parameter for non-serializable types
- **Expect:** UTF-8 output, custom serializers for complex types

### 13.3 Protocol Buffers / MessagePack / Other Formats

#### **[SER-3]** Major Issues
- **Flag:** Schema changes breaking backward compatibility
- **Flag:** Missing schema versioning
- **Flag:** Performance-critical paths using JSON when binary format appropriate
- **Expect:** Backward-compatible schema evolution, versioning, appropriate format choice

---

## 14. Messaging Patterns

### 14.1 Event-Driven Architecture

#### **[MSG-1]** Critical Issues
- **Flag:** Event handlers with side effects that aren't idempotent
- **Flag:** Missing error handling in event consumers
- **Flag:** Events with entire entities instead of IDs/minimal data
- **Flag:** Missing dead-letter handling for failed messages
- **Expect:** Idempotent handlers, error handling, lean event payloads, DLQ

#### **[MSG-2]** Major Issues
- **Flag:** Missing event schema versioning
- **Flag:** Tight coupling between publisher and subscriber
- **Flag:** Missing event ordering guarantees when required
- **Flag:** Synchronous event handling when async is appropriate
- **Expect:** Schema versioning, loose coupling, ordering where needed

### 14.2 Message Queues (RabbitMQ, Kafka, SQS)

#### **[MSG-3]** Critical Issues
- **Flag:** Messages acknowledged before processing completes
- **Flag:** Sensitive data in message payloads without encryption
- **Flag:** Missing poison message handling
- **Expect:** Ack after processing, data protection, poison message strategies

#### **[MSG-4]** Major Issues
- **Flag:** Missing message deduplication
- **Flag:** Consumer without proper connection recovery
- **Flag:** Hardcoded queue/topic names
- **Expect:** Deduplication, auto-reconnect, configurable queue names

---

## 15. Feature Management

### 15.1 Major Issues

- **Flag:** Feature checks scattered throughout code
- **Flag:** Missing default values for feature flags
- **Flag:** Feature flags in domain logic (should be application layer)
- **Flag:** Long-lived feature flags without cleanup plan
- **Flag:** Boolean feature flags for multi-variant features
- **Expect:** Centralized feature checks, defaults, application layer only

### 15.2 Implementation

#### **[FM-1]** Major Issues
- **Flag:** Hardcoded feature flags (no dynamic toggling)
- **Flag:** Missing feature flag configuration source (env vars, config service)
- **Flag:** Feature flag evaluation with side effects
- **Expect:** External configuration, clean evaluation, proper abstraction

### 15.3 Minor Issues

- **Flag:** Feature flag names not following convention
- **Flag:** Missing telemetry for feature usage
- **Flag:** Stale feature flags not removed after full rollout
- **Expect:** Consistent naming (`FEATURE_*`), usage tracking, cleanup schedule

---

## 16. Dependency Management

### 16.1 Critical Issues

- **Flag:** Packages with known vulnerabilities
- **Flag:** Packages from untrusted sources (non-PyPI, unsigned)
- **Flag:** Missing pinned versions in production (`requirements.txt` without versions)
- **Flag:** Using `pip install` without hash checking in CI/CD
- **Expect:** `pip-audit` / `safety` scanning, trusted sources, pinned versions, lock files

### 16.2 Major Issues

- **Flag:** Outdated packages with security patches available
- **Flag:** Conflicting dependency versions
- **Flag:** Missing lock file (`poetry.lock`, `Pipfile.lock`, `requirements.txt` with hashes)
- **Flag:** Unused dependencies in requirements
- **Flag:** Dev dependencies in production requirements
- **Expect:** Regular updates, lock files, minimal production dependencies

### 16.3 Minor Issues

- **Flag:** Not using modern dependency management (Poetry, PDM, uv)
- **Flag:** Missing dependency groups (dev, test, docs)
- **Flag:** Inconsistent dependency specification formats
- **Expect:** Modern tooling, organized dependency groups, consistent format

---

## 17. Testing

### 17.1 Unit Testing

#### **[TEST-1]** Critical Issues
- **Flag:** Tests with no assertions
- **Flag:** Tests that always pass (tautologies)
- **Flag:** Tests modifying shared state without cleanup
- **Flag:** Tests calling production external services
- **Expect:** Meaningful assertions, proper test isolation, mocks for external services

#### **[TEST-2]** Major Issues
- **Flag:** Missing test coverage for critical paths
- **Flag:** Overly complex test setup (indicates SUT design issues)
- **Flag:** Testing implementation details instead of behavior
- **Flag:** Missing edge case coverage (None, empty, boundary values)
- **Flag:** Hardcoded magic values without explanation
- **Flag:** Missing `conftest.py` for shared fixtures
- **Expect:** Behavior-focused tests, clear Arrange-Act-Assert, shared fixtures

#### **[TEST-3]** Minor Issues
- **Flag:** Non-descriptive test names (`test_1`, `test_func`)
- **Flag:** Duplicate test setup code (use fixtures)
- **Flag:** Missing test markers/categories (`@pytest.mark.slow`, `@pytest.mark.integration`)
- **Expect:** Descriptive naming (`test_should_*` or `test_<method>_<scenario>_<expected>`), fixtures, markers

### 17.2 Integration Testing

#### **[TEST-4]** Major Issues
- **Flag:** Integration tests without database cleanup/rollback
- **Flag:** Tests depending on external service availability
- **Flag:** Missing `TestClient` usage for API tests (FastAPI/Flask)
- **Flag:** Hardcoded ports, hostnames, or connection strings
- **Expect:** Testcontainers, proper isolation, test clients, configurable endpoints

### 17.3 Mocking

#### **[TEST-5]** Major Issues
- **Flag:** Over-mocking (mocking the SUT itself)
- **Flag:** `unittest.mock.patch` on wrong import path
- **Flag:** Missing `spec=True` on mocks (allows calling non-existent methods)
- **Flag:** Mocking builtins without restoration
- **Expect:** Mock at boundaries, correct patch targets, `spec=True`, proper cleanup

### 17.4 Property-Based Testing

#### **[TEST-6]** Minor Issues
- **Flag:** Missing property-based tests for pure functions with complex input spaces
- **Flag:** Missing `hypothesis` strategies for custom types
- **Expect:** `hypothesis` for data-intensive functions, custom strategies

---

## 18. Logging & Observability

### 18.1 Critical Issues
- **Flag:** Logging sensitive data (credentials, PII, tokens)
- **Flag:** Missing exception logging in except blocks
- **Flag:** No logging in critical business operations
- **Flag:** `print()` statements in production code
- **Expect:** Structured logging, sensitive data exclusion, proper `logging` module usage

### 18.2 Major Issues
- **Flag:** f-string formatting in log messages (use `%s`-style or structured logging)
  - Bad: `logger.info(f"User {user_id} logged in")`
  - Good: `logger.info("User %s logged in", user_id)` or structured: `logger.info("User logged in", extra={"user_id": user_id})`
- **Flag:** Incorrect log levels (ERROR for non-errors, DEBUG messages in production)
- **Flag:** Missing correlation IDs for request tracing
- **Flag:** Excessive logging in hot paths (performance impact)
- **Flag:** Root logger configuration polluting library loggers
- **Expect:** `logging.getLogger(__name__)`, structured logging (`structlog`, `python-json-logger`), appropriate levels

### 18.3 Health Checks
- **Flag:** Missing health check endpoints for external dependencies
- **Flag:** Health checks that could cause cascading failures
- **Flag:** Long-running health check operations
- **Flag:** Missing readiness vs liveness distinction in Kubernetes environments
- **Expect:** Lightweight health checks, proper dependency checks, `/health` and `/ready` endpoints

### 18.4 Metrics & Tracing
- **Flag:** Missing metrics for critical business operations
- **Flag:** Missing distributed tracing for microservices
- **Flag:** High-cardinality metric labels
- **Expect:** Prometheus metrics, OpenTelemetry tracing, bounded label cardinality

---

## 19. Project & Code Structure

### 19.1 Project Structure

#### **[PROJ-1]** Expected Structure (Application)
```
project_name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── domain/                # Enterprise business rules
│       │   ├── entities/
│       │   ├── value_objects/
│       │   ├── events/
│       │   ├── exceptions.py
│       │   └── interfaces/       # Repository protocols
│       ├── application/           # Application business rules
│       │   ├── use_cases/
│       │   ├── dto/
│       │   ├── interfaces/       # Infrastructure protocols
│       │   └── services/
│       ├── infrastructure/        # External concerns
│       │   ├── database/
│       │   ├── repositories/
│       │   ├── external_services/
│       │   └── config.py
│       └── presentation/          # API / Web
│           ├── api/
│           │   ├── v1/
│           │   └── dependencies.py
│           ├── middleware/
│           └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── pyproject.toml
├── README.md
└── .env.example
```

#### **[PROJ-2]** Critical Structure Issues
- **Flag:** Domain package importing infrastructure
- **Flag:** Application package importing presentation
- **Flag:** No separation between layers (everything in one flat package)
- **Expect:** Clear package boundaries, proper import hierarchy

#### **[PROJ-3]** Major Structure Issues
- **Flag:** Mixed responsibilities in single module
- **Flag:** Inconsistent package organization
- **Flag:** Missing `__init__.py` for public API definition
- **Flag:** Tests not mirroring source structure
- **Expect:** Consistent organization, clean public API, mirrored test structure

### 19.2 Module Organization

#### **[PROJ-4]** Major Issues
- **Flag:** Circular imports between modules
- **Flag:** Module doing too many things (>500 lines without good reason)
- **Flag:** Import side effects at module level
- **Expect:** Clean import hierarchy, focused modules, lazy initialization

### 19.3 File Organization

#### **[PROJ-5]** Major Issues
- **Flag:** Multiple unrelated classes in single file
- **Flag:** File name not matching primary class/function
- **Flag:** Missing `__all__` in `__init__.py` for public API
- **Expect:** One primary class per file, descriptive file names, explicit exports

### 19.4 Class Organization

#### **[PROJ-6]** Recommended Member Order
```python
class Example:
    # 1. Class variables / constants
    # 2. __init__ (constructor)
    # 3. __post_init__ (dataclass)
    # 4. Class methods (@classmethod) / factory methods
    # 5. Static methods (@staticmethod)
    # 6. Properties (@property)
    # 7. Public methods
    # 8. Protected methods (_single_underscore)
    # 9. Private methods (__double_underscore)
    # 10. Dunder methods (__str__, __repr__, etc.)
```

#### **[PROJ-7]** Minor Issues
- **Flag:** Inconsistent member ordering within project
- **Flag:** Related methods not grouped together
- **Expect:** Consistent ordering, logical grouping

---

## 20. Anti-Patterns to Flag

### Critical Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Blocking in async | Event loop starvation, deadlocks | `asyncio.to_thread()`, async libraries |
| `eval()`/`exec()` with user input | Remote code execution | Parsing libraries, AST |
| God Module | Unmaintainable, circular imports | Split into focused modules |
| Mutable default arguments | Shared state between calls | `None` default with conditional |
| Global mutable state | Thread safety issues, testing difficulty | Dependency injection, immutable config |

### Major Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Primitive Obsession | Lost type safety, validation scattered | Value objects, `NewType`, dataclasses |
| Anemic Domain Model | Logic scattered in services | Rich domain models |
| Magic Strings/Numbers | Maintenance nightmare | Constants, enums, configuration |
| Boolean Parameters | Unclear call sites | Enums, separate methods, keyword arguments |
| Deep Nesting | Readability issues | Early returns, guard clauses |
| High Cyclomatic Complexity | Hard to test and maintain | Break down, Strategy pattern |
| Code Duplication (DRY) | Maintenance overhead | Extract shared logic to functions/base classes |
| Wildcard Imports (`from x import *`) | Namespace pollution, unclear dependencies | Explicit imports |
| Bare `except:` | Catches `SystemExit`, `KeyboardInterrupt` | `except Exception:` minimum |
| Premature Optimization | Complexity without proven need | Profile first, optimize measured bottlenecks |
| Callback Hell | Deeply nested callbacks | `async`/`await`, promise chains |

### Minor Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Comments explaining what | Indicates unclear code | Self-documenting code |
| Commented-out code | Version control exists | Delete it |
| Dead/Unused Code | Clutters the codebase | Remove unused imports, functions, variables |
| Single-letter variables | Unclear intent (except `i`, `j` in loops) | Descriptive names |
| Overly long functions | Hard to understand and test | Extract helper functions |
| `type()` for type checking | Misses subclasses | `isinstance()` |

---

## 21. Naming & Style (PEP 8 Conventions)

### Major Issues
- **Flag:** Non-snake_case function and variable names
- **Flag:** Non-PascalCase class names
- **Flag:** Non-UPPER_SNAKE_CASE constants
- **Flag:** Inconsistent naming within a file/project
- **Flag:** Single-character names outside of comprehensions and loop variables
- **Flag:** Names that shadow built-ins (`list`, `dict`, `type`, `id`, `input`)

### Minor Issues
- **Flag:** Missing leading underscore on internal/private members
- **Flag:** Double leading underscore (name mangling) without justification
- **Flag:** Module names not lowercase and short
- **Flag:** Boolean variables/functions not using `is_`, `has_`, `can_`, `should_` prefixes
- **Flag:** Inconsistent import ordering (stdlib → third-party → local)
- **Flag:** Lines exceeding project's configured max length (typically 88-120 characters)
- **Flag:** Missing blank lines between top-level definitions

---

## 22. Modern Python 3.11+ Features

### Encourage Usage When Applicable
- `match`/`case` statements for complex branching (structural pattern matching)
- Exception groups and `except*` for concurrent error handling
- `TaskGroup` for structured concurrency
- `tomllib` for TOML parsing (stdlib in 3.11)
- `StrEnum` for string enumerations
- `Self` type for method return annotations
- `type` statement for type aliases (3.12+)
- f-string improvements (nested quotes, multiline in 3.12+)
- `@override` decorator for explicit method overriding (3.12+)
- `Unpack` for TypedDict unpacking in function signatures

### Flag Legacy Patterns
- **Flag:** `os.path` when `pathlib.Path` is cleaner
- **Flag:** `%` string formatting or `.format()` when f-strings are clearer
- **Flag:** `typing.Optional[X]` when `X | None` is available (3.10+)
- **Flag:** `typing.Union[X, Y]` when `X | Y` is available (3.10+)
- **Flag:** `typing.List`, `typing.Dict`, `typing.Tuple` when `list`, `dict`, `tuple` work (3.9+)
- **Flag:** Manual `__init__` when `@dataclass` or `@attrs` is appropriate
- **Flag:** `asyncio.get_event_loop()` instead of `asyncio.run()` for script entry points
- **Flag:** `datetime.utcnow()` (deprecated in 3.12) instead of `datetime.now(tz=timezone.utc)`

---

## Review Checklist Summary

Before approving, verify no issues exist in these categories:

### Must Check (Critical)
- [ ] No SQL injection or command injection vulnerabilities
- [ ] No hardcoded secrets or credentials
- [ ] Authentication/authorization properly implemented
- [ ] No blocking calls in async code
- [ ] Resources properly managed (context managers)
- [ ] No mutable default arguments
- [ ] No unsafe deserialization (`pickle`, `yaml.load`)
- [ ] Layer dependencies correct (Clean Architecture)
- [ ] Domain has no infrastructure dependencies

### Should Check (Major)
- [ ] Proper async/await usage throughout
- [ ] No N+1 query patterns
- [ ] Proper exception handling (specific types, logging)
- [ ] Type annotations present and correct
- [ ] API follows REST conventions
- [ ] Tests cover critical paths
- [ ] Logging is appropriate (no sensitive data, structured)
- [ ] Validation present on all inputs
- [ ] Resiliency patterns for external calls (timeouts, retries)
- [ ] Configuration centralized with validation
- [ ] SOLID principles followed
- [ ] Dependency management with lock files

### Could Check (Minor)
- [ ] Naming follows PEP 8 conventions
- [ ] Code is readable and well-organized
- [ ] Modern Python features used appropriately
- [ ] Documentation present where needed (docstrings)
- [ ] Consistent project structure
- [ ] Import ordering follows convention

---

*Last updated: February 2026 | Target: Python 3.11+*

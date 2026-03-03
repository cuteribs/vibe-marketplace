# .NET Code Review Guidelines for AI Reviewers

> **Target:** .NET 8+ (LTS) | **Audience:** Junior to Architect | **Scope:** Web APIs, Web Apps, Microservices, Libraries

This document provides comprehensive guidelines for AI-powered code review of .NET projects. Only negative issues should be reported using the severity classification below.

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
5. [Clean Architecture & DDD](#5-clean-architecture--ddd)
6. [API Design](#6-api-design)
7. [Data Access](#7-data-access)
8. [Validation Patterns](#8-validation-patterns)
9. [Configuration Management](#9-configuration-management)
10. [Middleware & Pipeline](#10-middleware--pipeline)
11. [Background Services](#11-background-services)
12. [Resiliency Patterns](#12-resiliency-patterns)
13. [Serialization](#13-serialization)
14. [Messaging Patterns](#14-messaging-patterns)
15. [Feature Management](#15-feature-management)
16. [Dependency Management](#16-dependency-management)
17. [Testing](#17-testing)
18. [Logging & Observability](#18-logging--observability)
19. [Project & Code Structure](#19-project--code-structure)
20. [Anti-Patterns to Flag](#20-anti-patterns-to-flag)
21. [Naming & Style](#21-naming--style-microsoft-conventions)
22. [Modern .NET 8+ Features](#22-modern-net-8-features)

---

## 1. Security Review

### 1.1 Critical Security Issues

#### **[SEC-1]** SQL Injection
- **Flag:** String concatenation or interpolation in SQL queries
- **Flag:** Raw SQL without parameterization in EF Core (`FromSqlRaw`, `ExecuteSqlRaw`)
- **Expect:** Parameterized queries, `FromSqlInterpolated`, or LINQ

#### **[SEC-2]** Cross-Site Scripting (XSS)
- **Flag:** `Html.Raw()` with user-controlled input
- **Flag:** Disabling request validation without justification
- **Expect:** Proper encoding, Content Security Policy headers

#### **[SEC-3]** Authentication & Authorization
- **Flag:** Missing `[Authorize]` on sensitive endpoints
- **Flag:** Hardcoded credentials, API keys, or connection strings
- **Flag:** Weak password policies or missing password hashing
- **Flag:** JWT tokens without expiration or proper validation
- **Flag:** Missing anti-forgery tokens on state-changing operations
- **Flag:** `[AllowAnonymous]` on endpoints that should be protected
- **Expect:** `[Authorize]` with appropriate policies, secrets in configuration/vault

#### **[SEC-4]** Sensitive Data Exposure
- **Flag:** Logging sensitive data (passwords, tokens, PII)
- **Flag:** Returning sensitive data in API responses unnecessarily
- **Flag:** Storing sensitive data in plain text
- **Flag:** Sensitive data in query strings (visible in logs/history)
- **Expect:** Data masking, encryption at rest, minimal data exposure

#### **[SEC-5]** Insecure Deserialization
- **Flag:** `BinaryFormatter`, `NetDataContractSerializer`, `SoapFormatter`
- **Flag:** `TypeNameHandling.All` or `TypeNameHandling.Auto` in JSON.NET
- **Expect:** `System.Text.Json` or JSON.NET with safe settings

#### **[SEC-6]** Path Traversal
- **Flag:** User input in file paths without validation
- **Expect:** `Path.GetFullPath()` with base path validation

#### **[SEC-7]** CORS Misconfiguration
- **Flag:** `AllowAnyOrigin()` combined with `AllowCredentials()`
- **Flag:** Wildcard origins in production
- **Expect:** Explicit origin whitelist

### 1.2 Major Security Issues

#### **[SEC-8]** Cryptography
- **Flag:** MD5, SHA1 for security purposes (acceptable for checksums)
- **Flag:** ECB mode encryption
- **Flag:** Hardcoded encryption keys or IVs
- **Flag:** Custom cryptography implementations
- **Expect:** SHA256+, AES-GCM, keys from secure storage

#### **[SEC-9]** Input Validation
- **Flag:** Missing validation on API inputs
- **Flag:** Missing `[FromBody]`, `[FromQuery]` explicit binding
- **Flag:** Accepting unbounded collections without limits
- **Expect:** FluentValidation or DataAnnotations, explicit model binding

#### **[SEC-10]** HTTP Security Headers
- **Flag:** Missing security headers (HSTS, X-Content-Type-Options, etc.)
- **Expect:** Security headers middleware configured

---

## 2. Performance Review

### 2.1 Critical Performance Issues

#### **[PERF-1]** Async/Await Anti-Patterns
- **Flag:** `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` (sync-over-async)
- **Flag:** `async void` (except event handlers)
- **Flag:** Missing `ConfigureAwait(false)` in library code
- **Flag:** `Task.Run()` wrapping already async methods
- **Expect:** Proper async propagation, `ValueTask` for hot paths

#### **[PERF-2]** Memory Leaks
- **Flag:** Event handlers not unsubscribed
- **Flag:** `IDisposable` not disposed (missing `using` or `await using`)
- **Flag:** Static references to request-scoped objects
- **Flag:** Capturing `HttpContext` in background tasks
- **Expect:** `using` statements, proper disposal patterns

#### **[PERF-3]** N+1 Query Problems
- **Flag:** LINQ queries inside loops
- **Flag:** Missing `.Include()` for required navigation properties
- **Flag:** Lazy loading enabled without justification
- **Expect:** Eager loading, batch queries, projections

### 2.2 Major Performance Issues

#### **[PERF-4]** Collection Operations
- **Flag:** Multiple enumerations of `IEnumerable<T>` (call `.ToList()` once)
- **Flag:** `Count() > 0` instead of `Any()`
- **Flag:** `FirstOrDefault()` then null check instead of `Any()` with predicate
- **Flag:** LINQ chain with multiple `Where()` that could be combined
- **Flag:** Using `List<T>` when `IReadOnlyList<T>` or array suffices
- **Expect:** Single enumeration, appropriate LINQ methods

#### **[PERF-5]** String Operations
- **Flag:** String concatenation in loops (use `StringBuilder`)
- **Flag:** `String.Format` in hot paths (use interpolation or `StringBuilder`)
- **Flag:** Case-insensitive comparison without `StringComparison` parameter
- **Expect:** `StringBuilder` for loops, `StringComparison.OrdinalIgnoreCase`

#### **[PERF-6]** Boxing/Allocations
- **Flag:** Value types used with non-generic collections
- **Flag:** Excessive LINQ in hot paths without benchmarking
- **Flag:** Closures capturing variables unnecessarily
- **Expect:** Generics, `Span<T>`, `stackalloc` where appropriate

#### **[PERF-7]** Database Performance
- **Flag:** `AsNoTracking()` missing for read-only queries
- **Flag:** Loading entire entities when projection would suffice
- **Flag:** Missing indexes hinted by query patterns
- **Flag:** Unbounded queries without pagination
- **Expect:** Projections, `AsNoTracking()`, pagination

#### **[PERF-8]** Caching
- **Flag:** Expensive operations repeated without caching consideration
- **Flag:** Cache keys that could collide
- **Flag:** Missing cache invalidation strategy
- **Expect:** `IMemoryCache` or `IDistributedCache` for expensive operations

### 2.3 Minor Performance Issues

- **Flag:** `DateTime.Now` instead of `DateTime.UtcNow` (perf + timezone issues)
- **Flag:** Regex without `RegexOptions.Compiled` for reused patterns
- **Flag:** `Enum.Parse` without caching in hot paths
- **Expect:** Source-generated regex (.NET 7+), `UtcNow`, cached conversions

---

## 3. Code Correctness

### 3.1 Critical Correctness Issues

#### **[CORR-1]** Null Reference Issues
- **Flag:** Possible null dereference without null checks
- **Flag:** Suppressing nullable warnings (`!`) without justification
- **Flag:** Missing null checks on external input
- **Expect:** Null-conditional operators, proper null guards, nullable reference types enabled

#### **[CORR-2]** Exception Handling
- **Flag:** Empty catch blocks (swallowing exceptions)
- **Flag:** Catching `Exception` without re-throwing or logging
- **Flag:** `throw ex` instead of `throw` (loses stack trace)
- **Flag:** Exception handling logic that alters program flow incorrectly
- **Expect:** Specific exception types, proper logging, `throw;` to rethrow

#### **[CORR-3]** Thread Safety
- **Flag:** Shared mutable state without synchronization
- **Flag:** Non-thread-safe collections used in concurrent scenarios
- **Flag:** Race conditions in singleton initialization
- **Flag:** Modifying collections while iterating
- **Expect:** `ConcurrentDictionary`, `lock`, `Interlocked`, immutable types

#### **[CORR-4]** Resource Management
- **Flag:** Database connections not disposed
- **Flag:** HTTP clients created per request (use `IHttpClientFactory`)
- **Flag:** File handles not closed in all code paths
- **Expect:** `using` statements, factory patterns, proper disposal

### 3.2 Major Correctness Issues

#### **[CORR-5]** Equality and Comparison
- **Flag:** Reference equality on value objects
- **Flag:** `GetHashCode()` override without `Equals()` or vice versa
- **Flag:** Mutable fields in `GetHashCode()`
- **Expect:** Proper equality implementation, records for value semantics

#### **[CORR-6]** Async Correctness
- **Flag:** Returning null instead of `Task.CompletedTask` or `Task.FromResult`
- **Flag:** Missing cancellation token propagation
- **Flag:** Fire-and-forget tasks without exception handling
- **Expect:** Cancellation token support, proper task handling

#### **[CORR-7]** Date/Time Handling
- **Flag:** `DateTime` used for UTC times (use `DateTimeOffset`)
- **Flag:** Time zone assumptions
- **Flag:** Date comparisons without considering time component
- **Expect:** `DateTimeOffset`, `TimeProvider` (.NET 8+), explicit timezone handling

---

## 4. Architecture & Design

### 4.1 Critical Architecture Issues

#### **[ARCH-1]** Dependency Injection
- **Flag:** `new`-ing services that should be injected
- **Flag:** Service Locator pattern (`IServiceProvider.GetService` in business logic)
- **Flag:** Captive dependencies (singleton depending on scoped)
- **Flag:** Circular dependencies
- **Expect:** Constructor injection, proper lifetime management

#### **[ARCH-2]** Layer Violations
- **Flag:** Domain/business logic depending on infrastructure
- **Flag:** Controllers containing business logic
- **Flag:** Data access in presentation layer
- **Flag:** Cross-cutting concerns scattered instead of centralized
- **Expect:** Clean Architecture boundaries, proper separation of concerns

### 4.2 Major Architecture Issues

#### **[ARCH-3]** SOLID Principles
- **Flag:** Classes with multiple responsibilities (SRP violation)
- **Flag:** God classes / methods exceeding reasonable size
- **Flag:** Tight coupling to concrete implementations (DIP violation)
- **Flag:** Interface segregation violations (large interfaces)
- **Expect:** Small focused classes, dependency on abstractions

#### **[ARCH-4]** Design Patterns
- **Flag:** Incorrect pattern implementation
- **Flag:** Over-engineering simple solutions
- **Flag:** Missing appropriate patterns (e.g., Strategy for conditionals)
- **Expect:** Appropriate pattern usage, KISS principle

---

## 5. Clean Architecture & DDD

### 5.1 Layer Responsibilities

#### **[CLEAN-1]** Domain Layer (Core/Entities)
**Purpose:** Contains enterprise business rules, entities, value objects, domain events, and domain services.

##### Critical Issues
- **Flag:** Infrastructure dependencies (EF Core, HTTP clients, file I/O)
- **Flag:** Framework dependencies (ASP.NET Core, Newtonsoft.Json)
- **Flag:** Database annotations (`[Key]`, `[Table]`, `[Column]`)
- **Flag:** References to Application, Infrastructure, or Presentation layers
- **Expect:** Pure C# with no external dependencies, self-contained business logic

##### Major Issues
- **Flag:** Anemic entities (only properties, no behavior)
- **Flag:** Public setters on entity properties without invariant protection
- **Flag:** Missing domain validation in entity constructors/methods
- **Flag:** Domain events not raised for significant state changes
- **Flag:** Primitive obsession (using `string`, `int` instead of value objects)
- **Expect:** Rich domain models, encapsulated state, value objects for concepts

##### Entity Guidelines
- **Flag:** Entities without identity (missing Id property/field)
- **Flag:** Mutable value objects
- **Flag:** Direct collection exposure (`public List<T>` instead of `IReadOnlyCollection<T>`)
- **Flag:** Business rules in services that belong in entities
- **Expect:** Protected setters, factory methods, domain methods for state changes

##### Aggregate Guidelines
- **Flag:** Aggregates too large (performance issues)
- **Flag:** References between aggregates by object instead of ID
- **Flag:** Missing aggregate root validation
- **Flag:** Child entities accessible without going through aggregate root
- **Expect:** Small aggregates, ID references, root controls children

#### **[CLEAN-2]** Application Layer
**Purpose:** Contains application business rules, use cases, commands/queries, DTOs, and interfaces for infrastructure.

##### Critical Issues
- **Flag:** Direct infrastructure implementations (DbContext, HttpClient usage)
- **Flag:** Domain entities returned to presentation layer
- **Flag:** References to Presentation or Infrastructure layers
- **Expect:** Depends only on Domain layer, defines interfaces implemented by Infrastructure

##### Major Issues
- **Flag:** Business logic that belongs in Domain layer
- **Flag:** Missing command/query separation (when using CQRS)
- **Flag:** Services doing too much (violating SRP)
- **Flag:** Missing input validation before domain operations
- **Flag:** Transaction management logic scattered across handlers
- **Expect:** Orchestration logic only, thin handlers, clear use cases

##### Interface Definitions
- **Flag:** Infrastructure-specific types in interface definitions
- **Flag:** Overly broad interfaces (interface segregation violation)
- **Flag:** Missing async methods for I/O operations
- **Expect:** Clean abstractions, specific interfaces, async by default

##### DTO Guidelines
- **Flag:** DTOs with behavior (methods other than simple transforms)
- **Flag:** Domain entities used as DTOs
- **Flag:** DTOs exposing internal IDs unnecessarily
- **Flag:** Missing mapping configuration (AutoMapper, Mapster)
- **Expect:** Simple data carriers, explicit mapping, versioned DTOs for APIs

#### **[CLEAN-3]** Infrastructure Layer
**Purpose:** Contains implementations of interfaces defined in Application layer, external service integrations, database access.

##### Critical Issues
- **Flag:** Business logic in infrastructure implementations
- **Flag:** Domain layer depending on infrastructure types
- **Flag:** Infrastructure types exposed through Application interfaces
- **Expect:** Implements Application interfaces, contains only technical concerns

##### Major Issues
- **Flag:** Repository methods with business logic
- **Flag:** Missing unit of work pattern for transactions
- **Flag:** Direct DbContext injection in Application layer
- **Flag:** External service calls without abstraction
- **Expect:** Pure data access, proper abstractions, isolated external dependencies

##### Repository Guidelines
- **Flag:** Generic repository hiding EF Core capabilities
- **Flag:** Repository returning `IQueryable` (leaky abstraction)
- **Flag:** Missing specification pattern for complex queries
- **Flag:** CRUD repositories for read-heavy scenarios
- **Expect:** Specific repositories, materialized returns, CQRS for complex reads

#### **[CLEAN-4]** Presentation Layer (API/Web)
**Purpose:** Contains controllers, view models, API endpoints, middleware, and DI configuration.

##### Critical Issues
- **Flag:** Business logic in controllers
- **Flag:** Direct domain entity manipulation
- **Flag:** Infrastructure dependencies (DbContext) in controllers
- **Expect:** Thin controllers, delegates to Application layer

##### Major Issues
- **Flag:** Missing input validation attributes
- **Flag:** Domain exceptions not mapped to HTTP responses
- **Flag:** Inconsistent response formats
- **Flag:** Missing API versioning
- **Expect:** Validation, exception handling middleware, consistent responses

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
- Presentation → Infrastructure (DI registration only) ✓
- Presentation → Application (Indirect thru Infrastructure) ✓
- Infrastructure → Application (interface implementation) ✓
- Infrastructure → Domain (Indirect thru Application) ✓
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
- **Expect:** Single responsibility, pipeline behaviors for cross-cutting

### 5.4 Domain Events

- **Flag:** Domain events raised outside aggregate methods
- **Flag:** Missing event handlers for published events
- **Flag:** Side effects in event raise (should be handled by handlers)
- **Flag:** Events containing entire entities instead of IDs/data
- **Expect:** Events raised in domain, handled in application/infrastructure

---

## 6. API Design

### 6.1 Critical API Issues

#### **[API-1]** REST Conventions
- **Flag:** GET endpoints modifying state
- **Flag:** Non-idempotent PUT operations
- **Flag:** Missing HTTP status codes for error cases
- **Flag:** Exposing internal exceptions in responses
- **Expect:** Proper HTTP verbs, Problem Details for errors (RFC 7807)

#### **[API-2]** Error Handling
- **Flag:** Inconsistent error response format
- **Flag:** Stack traces in production error responses
- **Flag:** Generic 500 errors without logging
- **Expect:** Global exception handling, structured error responses

### 6.2 Major API Issues

#### **[API-3]** Versioning
- **Flag:** Breaking changes without version bump
- **Flag:** Missing API versioning strategy
- **Expect:** URL or header-based versioning, backward compatibility

#### **[API-4]** Request/Response Design
- **Flag:** Overly large request/response objects
- **Flag:** Missing pagination on collection endpoints
- **Flag:** Circular references in serialization
- **Flag:** Exposing internal IDs unnecessarily
- **Expect:** DTOs, pagination, proper serialization settings

#### **[API-5]** Documentation
- **Flag:** Missing XML documentation on public APIs
- **Flag:** Swagger/OpenAPI not reflecting actual behavior
- **Flag:** Missing example values for complex types
- **Expect:** XML docs, accurate OpenAPI spec

### 6.3 Minor API Issues

- **Flag:** Inconsistent naming conventions in endpoints
- **Flag:** Missing `[ProducesResponseType]` attributes
- **Flag:** Hardcoded strings in route templates
- **Expect:** Consistent naming, explicit response types, constants for routes

---

## 7. Data Access

### 7.1 Entity Framework Core

#### **[DA-1]** Critical Issues
- **Flag:** Transactions not used for multi-entity operations
- **Flag:** SaveChanges in loops
- **Flag:** Missing migration for schema changes
- **Flag:** Synchronous database calls in async context
- **Expect:** Proper transaction handling, batch operations

#### **[DA-2]** Major Issues
- **Flag:** Business logic in repositories
- **Flag:** Generic repository anti-pattern (hiding EF capabilities)
- **Flag:** Missing `AsNoTracking()` for read operations
- **Flag:** Complex queries better suited for raw SQL
- **Flag:** Missing query splitting for cartesian explosion
- **Expect:** Specifications pattern, appropriate EF usage

#### **[DA-3]** Minor Issues
- **Flag:** Missing index configuration for frequently queried columns
- **Flag:** Implicit conversions in queries preventing index usage
- **Expect:** Proper indexing, explicit type handling

### 7.2 Dapper

#### **[DA-4]** Critical Issues
- **Flag:** SQL injection via string concatenation
- **Flag:** Missing parameter validation
- **Flag:** Connections not disposed
- **Expect:** Parameterized queries, `using` statements

#### **[DA-5]** Major Issues
- **Flag:** Manual mapping when AutoMapper/Mapster appropriate
- **Flag:** Large result sets without streaming
- **Expect:** Appropriate mapping, buffered vs unbuffered queries

---

## 8. Validation Patterns

### 8.1 Critical Issues

- **Flag:** Missing validation on untrusted input
- **Flag:** Validation bypassed by direct model binding
- **Flag:** Client-side only validation (no server-side)
- **Expect:** Server-side validation always, defense in depth

### 8.2 FluentValidation

#### **[VAL-1]** Major Issues
- **Flag:** Validators not registered in DI
- **Flag:** Business rules in validators (belongs in domain)
- **Flag:** Missing `CascadeMode` for dependent rules
- **Flag:** Async validation not used for I/O operations
- **Flag:** Complex validation logic not extracted to custom validators
- **Expect:** Registered validators, input validation only, proper async

#### **[VAL-2]** Minor Issues
- **Flag:** Duplicate validation rules across validators
- **Flag:** Missing custom error messages
- **Flag:** Overly complex rule chains
- **Expect:** Shared rules via inheritance/composition, clear messages

### 8.3 DataAnnotations

#### **[VAL-3]** Major Issues
- **Flag:** Missing `[Required]` on non-nullable reference types
- **Flag:** Missing range/length constraints on user input
- **Flag:** Custom validation attributes with side effects
- **Expect:** Complete annotations, pure validation logic

### 8.4 Domain Validation

#### **[VAL-4]** Major Issues
- **Flag:** Domain invariants not enforced in constructors
- **Flag:** Validation exceptions instead of Result pattern
- **Flag:** Validation scattered across application layer
- **Expect:** Guard clauses, Result/Either pattern, centralized in domain

---

## 9. Configuration Management

### 9.1 Critical Issues

- **Flag:** Secrets in appsettings.json (connection strings, API keys)
- **Flag:** Production settings in source control
- **Flag:** Missing configuration validation at startup
- **Expect:** User secrets for dev, Key Vault/env vars for prod, validation

### 9.2 Options Pattern

#### **[CONFIG-1]** Major Issues
- **Flag:** Direct `IConfiguration` injection in services
- **Flag:** Missing `IOptions<T>`, `IOptionsSnapshot<T>`, or `IOptionsMonitor<T>`
- **Flag:** Options classes without validation
- **Flag:** Mutable options classes
- **Flag:** Missing `[Required]` attributes on required options
- **Expect:** Strongly-typed options, validation, appropriate lifetime

#### **[CONFIG-2]** Minor Issues
- **Flag:** Options not organized by feature/section
- **Flag:** Missing default values where appropriate
- **Expect:** Organized configuration sections, sensible defaults

### 9.3 Environment-Specific Configuration

#### **[CONFIG-3]** Major Issues
- **Flag:** Environment checks in code instead of configuration
- **Flag:** Missing environment-specific transforms
- **Flag:** Hardcoded environment names
- **Expect:** Configuration transforms, environment abstraction

---

## 10. Middleware & Pipeline

### 10.1 Critical Issues

- **Flag:** Exception handling middleware not first in pipeline
- **Flag:** Authentication/authorization middleware order incorrect
- **Flag:** Request body read multiple times without buffering
- **Expect:** Correct middleware order, proper request handling

### 10.2 Major Issues

- **Flag:** Business logic in middleware (use filters or services)
- **Flag:** Missing `next()` call (breaks pipeline)
- **Flag:** Long-running operations in middleware blocking requests
- **Flag:** Request/response modification without proper stream handling
- **Flag:** Missing endpoint routing understanding
- **Expect:** Infrastructure concerns only, proper async, correct ordering

### 10.3 Minor Issues

- **Flag:** Duplicate middleware functionality
- **Flag:** Missing middleware documentation
- **Expect:** Single responsibility, clear purpose

### 10.4 Pipeline Order Guidelines

```
1. Exception handling
2. HSTS
3. HTTPS redirection
4. Static files
5. Routing
6. CORS
7. Authentication
8. Authorization
9. Custom middleware
10. Endpoints
```

---

## 11. Background Services

### 11.1 Critical Issues

- **Flag:** Unhandled exceptions killing the host
- **Flag:** Missing cancellation token respect
- **Flag:** Scoped services resolved in singleton hosted service
- **Flag:** Missing graceful shutdown handling
- **Expect:** Try-catch in `ExecuteAsync`, proper scoping, cancellation support

### 11.2 Major Issues

- **Flag:** Tight loops without delay
- **Flag:** Missing health checks for background services
- **Flag:** No retry logic for transient failures
- **Flag:** Blocking operations in `StartAsync`
- **Expect:** Appropriate delays, health reporting, resilience

### 11.3 IHostedService vs BackgroundService

- **Flag:** Long-running work in `IHostedService.StartAsync`
- **Flag:** `BackgroundService` without `ExecuteAsync` override
- **Expect:** `BackgroundService` for continuous work, `IHostedService` for startup/shutdown tasks

### 11.4 Scoped Service Access

- **Flag:** Direct `DbContext` injection in `BackgroundService`
- **Flag:** Missing `IServiceScopeFactory` for scoped dependencies
- **Expect:** Create scope for each unit of work

---

## 12. Resiliency Patterns

### 12.1 Critical Issues

- **Flag:** External calls without timeout
- **Flag:** Missing circuit breaker for external dependencies
- **Flag:** Retry on non-idempotent operations
- **Expect:** Timeouts, circuit breakers, idempotency awareness

### 12.2 Polly Integration

#### **[RES-1]** Major Issues
- **Flag:** Hardcoded retry counts/delays
- **Flag:** Retrying on all exceptions (should be selective)
- **Flag:** Missing jitter in retry delays
- **Flag:** Circuit breaker state not monitored
- **Flag:** Bulkhead not used for resource isolation
- **Expect:** Configurable policies, specific exceptions, jitter, monitoring

#### **[RES-2]** Minor Issues
- **Flag:** Policies not defined in DI (scattered across code)
- **Flag:** Missing policy documentation
- **Expect:** Centralized policy definitions, clear naming

### 12.3 HTTP Client Resiliency

#### **[RES-3]** Major Issues
- **Flag:** `HttpClient` without resilience policies
- **Flag:** Missing `HttpClientFactory`
- **Flag:** Infinite timeout or very long timeouts
- **Expect:** Resilience via `AddPolicyHandler`, appropriate timeouts

---

## 13. Serialization

### 13.1 Critical Issues

- **Flag:** `TypeNameHandling.All` or `Auto` in Newtonsoft.Json (RCE risk)
- **Flag:** Deserializing untrusted input without validation
- **Flag:** Circular reference handling that could cause stack overflow
- **Expect:** Safe serialization settings, input validation

### 13.2 System.Text.Json (Preferred)

#### **[SER-1]** Major Issues
- **Flag:** Missing `JsonSerializerOptions` configuration for APIs
- **Flag:** Ignoring serialization errors silently
- **Flag:** Missing source generators for performance-critical code
- **Flag:** Incorrect property naming policy
- **Expect:** Consistent options, source generators, proper error handling

#### **[SER-2]** Minor Issues
- **Flag:** Missing `[JsonPropertyName]` for non-standard names
- **Flag:** Enum serialization as numbers when strings preferred
- **Expect:** Explicit configuration, string enums

### 13.3 Newtonsoft.Json (Legacy)

#### **[SER-3]** Major Issues
- **Flag:** Default settings used (should be explicit)
- **Flag:** Missing `ReferenceLoopHandling`
- **Flag:** `DateTimeZoneHandling` not configured
- **Expect:** Explicit, safe configuration

---

## 14. Messaging Patterns

### 14.1 MediatR

#### **[MSG-1]** Critical Issues
- **Flag:** Handlers with side effects in pipeline
- **Flag:** Missing exception handling in handlers
- **Flag:** Circular handler dependencies
- **Expect:** Clean handlers, proper error handling

#### **[MSG-2]** Major Issues
- **Flag:** Notifications without any handlers
- **Flag:** Overly complex pipelines
- **Flag:** Request/handler in different assemblies without registration
- **Flag:** Missing validation pipeline behavior
- **Expect:** Handler registration, validation behavior, reasonable complexity

### 14.2 Message Queues (MassTransit, etc.)

#### **[MSG-3]** Critical Issues
- **Flag:** Messages without idempotency handling
- **Flag:** Missing dead-letter queue configuration
- **Flag:** Sensitive data in message payloads
- **Expect:** Idempotent consumers, DLQ, data protection

#### **[MSG-4]** Major Issues
- **Flag:** Missing message versioning strategy
- **Flag:** Consumers with external dependencies not handling failures
- **Flag:** Missing saga/state machine for complex workflows
- **Expect:** Versioning, retry policies, proper orchestration

---

## 15. Feature Management

### 15.1 Major Issues

- **Flag:** Feature checks scattered throughout code
- **Flag:** Missing default values for feature flags
- **Flag:** Feature flags in domain logic (should be application layer)
- **Flag:** Long-lived feature flags without cleanup plan
- **Expect:** Centralized checks, defaults, application layer only

### 15.2 Microsoft.FeatureManagement

#### **[FM-1]** Major Issues
- **Flag:** Missing `IFeatureManager` DI (using static checks)
- **Flag:** Feature filters without proper configuration
- **Flag:** Missing feature flag documentation
- **Expect:** DI-based feature management, documented flags

### 15.3 Minor Issues

- **Flag:** Feature flag names not following convention
- **Flag:** Missing telemetry for feature usage
- **Expect:** Consistent naming, usage tracking

---

## 16. Dependency Management

### 16.1 Critical Issues

- **Flag:** Packages with known vulnerabilities
- **Flag:** Packages from untrusted sources
- **Flag:** Missing package lock file in CI/CD
- **Expect:** Vulnerability scanning, trusted sources, reproducible builds

### 16.2 Major Issues

- **Flag:** Outdated packages with security patches available
- **Flag:** Conflicting package versions
- **Flag:** Direct dependency on transitive package
- **Flag:** Unnecessary packages (unused dependencies)
- **Flag:** Preview packages in production code
- **Expect:** Regular updates, version consistency, minimal dependencies

### 16.3 Minor Issues

- **Flag:** Inconsistent package versions across projects
- **Flag:** Missing `Directory.Packages.props` for centralized versioning
- **Expect:** Central package management, version alignment

---

## 17. Testing

### 17.1 Unit Testing

#### **[TEST-1]** Critical Issues
- **Flag:** Tests with no assertions
- **Flag:** Tests that always pass (tautologies)
- **Flag:** Tests modifying shared state without cleanup
- **Flag:** Tests calling production external services
- **Expect:** Meaningful assertions, proper test isolation

#### **[TEST-2]** Major Issues
- **Flag:** Missing test coverage for critical paths
- **Flag:** Overly complex test setup (indicates SUT design issues)
- **Flag:** Testing implementation details instead of behavior
- **Flag:** Missing edge case coverage (null, empty, boundary values)
- **Flag:** Hard-coded magic values without explanation
- **Expect:** Behavior-focused tests, clear Arrange-Act-Assert

#### **[TEST-3]** Minor Issues
- **Flag:** Non-descriptive test names
- **Flag:** Duplicate test setup code (use fixtures)
- **Flag:** Missing test categories/traits
- **Expect:** Descriptive naming, shared fixtures, proper organization

### 17.2 Integration Testing

#### **[TEST-4]** Major Issues
- **Flag:** Integration tests without database cleanup
- **Flag:** Tests depending on external service availability
- **Flag:** Missing `WebApplicationFactory` usage for API tests
- **Flag:** Hardcoded ports or connection strings
- **Expect:** Test containers, proper isolation, `WebApplicationFactory<T>`

### 17.3 E2E Testing

#### **[TEST-5]** Major Issues
- **Flag:** Brittle selectors (implementation-dependent)
- **Flag:** Missing wait strategies (race conditions)
- **Flag:** Tests not cleaning up created data
- **Expect:** Stable selectors, proper waits, test data management

---

## 18. Logging & Observability

### 18.1 Critical Issues
- **Flag:** Logging sensitive data (credentials, PII, tokens)
- **Flag:** Missing exception logging in catch blocks
- **Flag:** No logging in critical business operations
- **Expect:** Structured logging, sensitive data exclusion

### 18.2 Major Issues
- **Flag:** String interpolation in log messages (use structured logging)
- **Flag:** Incorrect log levels (Error for non-errors, Debug in production)
- **Flag:** Missing correlation IDs for request tracing
- **Flag:** Excessive logging in hot paths (performance impact)
- **Expect:** `ILogger<T>`, structured parameters, appropriate levels

### 18.3 Health Checks
- **Flag:** Missing health checks for external dependencies
- **Flag:** Health checks that could cause cascading failures
- **Flag:** Long-running health check operations
- **Expect:** Lightweight health checks, proper dependency checks

---

## 19. Project & Code Structure

### 19.1 Solution Structure (Clean Architecture)

#### **[PROJ-1]** Expected Structure
```
src/
├── Domain/                    # Enterprise business rules
│   ├── Entities/
│   ├── ValueObjects/
│   ├── Events/
│   ├── Exceptions/
│   └── Interfaces/           # Repository interfaces (optional)
├── Application/               # Application business rules
│   ├── Behaviors/        # Pipeline behaviors
│   ├── Interfaces/       # Infrastructure interfaces
│   ├── Mappings/
│   ├── Commands/
│   ├── Queries/
│   ├── DTOs/
│   └── DependencyInjection.cs
├── Infrastructure/            # External concerns
│   ├── Configurations/
│   ├── Repositories/
│   ├── ApplicationDbContext.cs
│   ├── Services/             # External service implementations
│   └── DependencyInjection.cs
└── Presentation/              # API/Web
    ├── Controllers/
    ├── Middleware/
    ├── Filters/
    └── Program.cs
```

#### **[PROJ-2]** Critical Structure Issues
- **Flag:** Domain project referencing Infrastructure
- **Flag:** Application project referencing Presentation
- **Flag:** Missing separation between layers
- **Expect:** Clear project boundaries, proper references

#### **[PROJ-3]** Major Structure Issues
- **Flag:** Mixed responsibilities in single project
- **Flag:** Feature folders inconsistently organized
- **Flag:** Missing `DependencyInjection.cs` per layer
- **Flag:** Shared projects without clear purpose
- **Expect:** Consistent organization, clear DI registration

### 19.2 Namespace Conventions

#### **[PROJ-4]** Major Issues
- **Flag:** Namespace not matching folder structure
- **Flag:** Inconsistent namespace patterns
- **Flag:** Root namespace too generic
- **Expect:** `Company.Product.Layer.Feature` pattern

### 19.3 File Organization

#### **[PROJ-5]** Major Issues
- **Flag:** Multiple public types in single file
- **Flag:** File name not matching type name
- **Flag:** Related types scattered across folders
- **Expect:** One public type per file, name matches type, cohesive organization

### 19.4 Class Organization

#### **[PROJ-6]** Recommended Member Order
```csharp
public class Example
{
    // 1. Constants
    // 2. Static fields
    // 3. Instance fields
    // 4. Constructors
    // 5. Properties
    // 6. Public methods
    // 7. Internal methods
    // 8. Protected methods
    // 9. Private methods
    // 10. Nested types
}
```

#### **[PROJ-7]** Minor Issues
- **Flag:** Inconsistent member ordering
- **Flag:** Related members not grouped together
- **Expect:** Consistent ordering within project

---

## 20. Anti-Patterns to Flag

### Critical Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Sync-over-async | Deadlocks, thread pool starvation | Async all the way |
| Service Locator | Hidden dependencies, testability issues | Constructor injection |
| God Class | Unmaintainable, violates SRP | Split into focused classes |
| Static abuse | Global state, testability issues | Dependency injection |

### Major Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Primitive Obsession | Lost type safety, validation scattered | Value objects, strong typing |
| Anemic Domain Model | Logic scattered in services | Rich domain models |
| Magic Strings/Numbers | Maintenance nightmare | Constants, enums, configuration |
| Boolean Parameters | Unclear call sites | Enums, separate methods |
| Deep Nesting | Readability issues | Early returns, guard clauses |
| High Cyclomatic Complexity | Hard to test and maintain | Break down into smaller methods, Strategy pattern |
| Code Duplication (DRY) | Maintenance overhead, bug replication | Extract shared logic to helper methods, base classes, or services |
| Temporal Coupling | Order-dependent method calls | Builder pattern, state machines |
| Train Wreck (`a.b.c.d`) | Law of Demeter violation | Encapsulation |
| Generic Repository | Hides ORM capabilities | Specific repositories |
| Leaky Abstraction | Implementation details exposed | Proper encapsulation |

### Minor Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Comments explaining what | Indicates unclear code | Self-documenting code |
| Commented-out code | Version control exists | Delete it |
| Dead/Unused Code | Clutters the codebase | Remove unused variables, private methods, or classes |
| Hungarian notation | Outdated convention | Modern C# naming |
| Regions in methods | Method too large | Extract methods |

---

## 21. Naming & Style (Microsoft Conventions)

### Major Issues
- **Flag:** Non-PascalCase public members
- **Flag:** Non-camelCase private fields without underscore prefix
- **Flag:** Abbreviations not following guidelines (use `Id` not `ID`)
- **Flag:** Inconsistent naming within a file/project

### Minor Issues
- **Flag:** Interfaces not prefixed with `I`
- **Flag:** Async methods not suffixed with `Async`
- **Flag:** Generic type parameters not prefixed with `T`
- **Flag:** Boolean properties/methods not using `Is`, `Has`, `Can` prefixes

---

## 22. Modern .NET 8+ Features

### Encourage Usage When Applicable
- Primary constructors for simple classes
- Collection expressions (`[1, 2, 3]`)
- `required` modifier for required properties
- File-scoped types for internal implementation
- `TimeProvider` for testable time operations
- `IExceptionHandler` for global exception handling
- Source generators over reflection
- `FrozenDictionary<K,V>` for read-heavy dictionaries

### Flag Legacy Patterns
- **Flag:** Manual JSON serialization when source generators available
- **Flag:** Reflection-based dependency registration when compile-time available
- **Flag:** `DateTime.Now` when `TimeProvider` would improve testability

---

## Review Checklist Summary

Before approving, verify no issues exist in these categories:

### Must Check (Critical)
- [ ] No SQL injection vulnerabilities
- [ ] No hardcoded secrets or credentials
- [ ] Authentication/authorization properly implemented
- [ ] No sync-over-async patterns
- [ ] Resources properly disposed
- [ ] No null reference risks
- [ ] Layer dependencies correct (Clean Architecture)
- [ ] Domain has no infrastructure dependencies

### Should Check (Major)
- [ ] Proper async/await usage
- [ ] No N+1 query patterns
- [ ] Proper exception handling
- [ ] DI used correctly (no captive dependencies)
- [ ] API follows REST conventions
- [ ] Tests cover critical paths
- [ ] Logging is appropriate (no sensitive data)
- [ ] Validation present on all inputs
- [ ] Resiliency patterns for external calls
- [ ] Configuration uses Options pattern
- [ ] SOLID principles followed

### Could Check (Minor)
- [ ] Naming follows conventions
- [ ] Code is readable and well-organized
- [ ] Modern C# features used appropriately
- [ ] Documentation present where needed
- [ ] Consistent project structure

---

*Last updated: January 2026 | Target: .NET 8+ LTS*

# Frontend Code Review Guidelines for AI Reviewers

> **Target:** Modern Frontend (ES2022+, TypeScript 5+) | **Audience:** Junior to Architect | **Scope:** SPAs, SSR/SSG Apps, Component Libraries, Design Systems, Progressive Web Apps

> **Tech Stack Coverage:** JavaScript, TypeScript, HTML, CSS/SCSS/Tailwind, React, Vue, Angular, Svelte, Next.js, Nuxt, Astro, Vite, Webpack

This document provides comprehensive guidelines for AI-powered code review of frontend projects. Only negative issues should be reported using the severity classification below.

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
5. [Component Design](#5-component-design)
6. [State Management](#6-state-management)
7. [API Integration & Data Fetching](#7-api-integration--data-fetching)
8. [Forms & Validation](#8-forms--validation)
9. [Routing & Navigation](#9-routing--navigation)
10. [Styling & CSS](#10-styling--css)
11. [Accessibility (a11y)](#11-accessibility-a11y)
12. [Internationalization (i18n)](#12-internationalization-i18n)
13. [Build & Bundling](#13-build--bundling)
14. [Testing](#14-testing)
15. [Error Handling & Observability](#15-error-handling--observability)
16. [HTML & Semantic Markup](#16-html--semantic-markup)
17. [TypeScript Usage](#17-typescript-usage)
18. [Dependency Management](#18-dependency-management)
19. [Project & Code Structure](#19-project--code-structure)
20. [Anti-Patterns to Flag](#20-anti-patterns-to-flag)
21. [Naming & Style Conventions](#21-naming--style-conventions)
22. [Modern Features & Best Practices](#22-modern-features--best-practices)

---

## 1. Security Review

### 1.1 Critical Security Issues

#### **[SEC-1]** Cross-Site Scripting (XSS)
- **Flag:** `dangerouslySetInnerHTML` (React) / `v-html` (Vue) / `[innerHTML]` (Angular) with user-controlled input
- **Flag:** Direct DOM manipulation with `innerHTML`, `outerHTML`, `document.write()`
- **Flag:** Unescaped user input rendered in templates
- **Flag:** `eval()`, `new Function()`, `setTimeout(string)` with user-controlled data
- **Flag:** URL injection via `href`, `src`, `action` attributes with `javascript:` protocol
- **Expect:** Framework auto-escaping, DOMPurify for HTML sanitization, `textContent` for text insertion

#### **[SEC-2]** Cross-Site Request Forgery (CSRF)
- **Flag:** State-changing API calls without CSRF tokens
- **Flag:** Cookies without `SameSite` attribute
- **Flag:** Missing CSRF protection on form submissions
- **Expect:** CSRF tokens, `SameSite=Strict` or `SameSite=Lax` cookies, anti-CSRF middleware

#### **[SEC-3]** Authentication & Token Management
- **Flag:** Tokens stored in `localStorage` (vulnerable to XSS)
- **Flag:** Sensitive data in `localStorage` or `sessionStorage`
- **Flag:** JWT tokens not validated on expiration client-side
- **Flag:** Missing token refresh logic (expired tokens sent to API)
- **Flag:** Credentials or API keys in client-side code or bundles
- **Flag:** Auth state managed only client-side without server validation
- **Expect:** `httpOnly` cookies for tokens, secure token refresh, no secrets in client code

#### **[SEC-4]** Sensitive Data Exposure
- **Flag:** API keys, secrets, or credentials in frontend source code
- **Flag:** Sensitive data in URL query parameters (visible in browser history)
- **Flag:** PII logged to browser console in production
- **Flag:** Source maps enabled in production exposing original source
- **Flag:** Sensitive data in error messages shown to users
- **Expect:** Environment variables via build-time injection, no secrets in client bundles, disabled source maps in prod

#### **[SEC-5]** Content Security Policy (CSP)
- **Flag:** Inline scripts without nonce or hash
- **Flag:** `unsafe-inline` or `unsafe-eval` in CSP directives
- **Flag:** Missing CSP headers entirely
- **Flag:** Overly permissive CSP (`*` sources)
- **Expect:** Strict CSP with nonces, no inline scripts/styles, report-uri configured

#### **[SEC-6]** Third-Party Script Injection
- **Flag:** External scripts loaded without `integrity` attribute (Subresource Integrity)
- **Flag:** Third-party scripts with full DOM access without sandboxing
- **Flag:** Dynamically loading scripts from user-controlled URLs
- **Expect:** SRI hashes, sandboxed iframes for third-party content, trusted CDN sources

#### **[SEC-7]** Open Redirect
- **Flag:** Redirect URLs taken from query parameters without validation
- **Flag:** `window.location` set from user input without URL validation
- **Expect:** Redirect URL allowlist, origin validation, relative paths only

### 1.2 Major Security Issues

#### **[SEC-8]** Dependency Security
- **Flag:** Known vulnerable npm packages (check `npm audit`)
- **Flag:** Packages with malicious post-install scripts
- **Flag:** Unpinned dependency versions in production
- **Expect:** Regular `npm audit`, lock files committed, pinned versions

#### **[SEC-9]** Input Sanitization
- **Flag:** User input used in CSS expressions (`style` attributes)
- **Flag:** User input in `RegExp` constructors (ReDoS risk)
- **Flag:** File uploads without type/size validation
- **Flag:** Rich text editors without HTML sanitization
- **Expect:** Input sanitization libraries, validated uploads, DOMPurify for rich text

#### **[SEC-10]** CORS & API Security
- **Flag:** Credentials sent to third-party APIs without necessity
- **Flag:** Sensitive headers exposed in CORS preflight
- **Flag:** API calls over HTTP instead of HTTPS
- **Expect:** HTTPS only, minimal credential sharing, proper CORS handling

---

## 2. Performance Review

### 2.1 Critical Performance Issues

#### **[PERF-1]** Bundle Size & Code Splitting
- **Flag:** Entire library imported when tree-shakeable import available (`import _ from 'lodash'` vs `import debounce from 'lodash/debounce'`)
- **Flag:** Large dependencies in main bundle without code splitting
- **Flag:** Missing lazy loading for route-level components
- **Flag:** Unused polyfills for modern browsers
- **Flag:** Moment.js used (large bundle; use `date-fns`, `dayjs`, or `Intl`)
- **Expect:** Dynamic `import()`, route-based code splitting, tree-shaking friendly imports

#### **[PERF-2]** Rendering Performance
- **Flag:** Missing `key` props on list items (React/Vue)
- **Flag:** Array index used as `key` on reorderable lists
- **Flag:** Large component re-renders without memoization
- **Flag:** Expensive calculations in render path without memoization
- **Flag:** Layout thrashing (reading then writing DOM in loops)
- **Flag:** Forced synchronous layouts (reading `offsetHeight` after style changes)
- **Expect:** Stable unique keys, `React.memo`/`useMemo`/`computed`, batched DOM operations

#### **[PERF-3]** Memory Leaks
- **Flag:** Event listeners not removed on component unmount
- **Flag:** Subscriptions (WebSocket, Observable) not cleaned up
- **Flag:** `setInterval`/`setTimeout` not cleared on unmount
- **Flag:** Closures capturing stale references in long-lived callbacks
- **Flag:** Detached DOM nodes held in references
- **Expect:** Cleanup in `useEffect` return / `onUnmounted` / `ngOnDestroy`, `AbortController` for fetch

### 2.2 Major Performance Issues

#### **[PERF-4]** Image & Media Optimization
- **Flag:** Unoptimized images (no compression, wrong format)
- **Flag:** Missing `width`/`height` attributes causing layout shift (CLS)
- **Flag:** Images not lazy-loaded below the fold
- **Flag:** Missing responsive images (`srcset`, `<picture>`)
- **Flag:** Videos autoplaying on mobile without user interaction
- **Expect:** WebP/AVIF format, `loading="lazy"`, responsive images, proper sizing

#### **[PERF-5]** Network Performance
- **Flag:** Waterfall requests that could be parallelized
- **Flag:** Missing request deduplication (same API called multiple times)
- **Flag:** No caching strategy for API responses
- **Flag:** Polling when WebSocket/SSE would be more efficient
- **Flag:** Large payloads without pagination
- **Expect:** Parallel requests, request deduplication (React Query/SWR/TanStack Query), caching, pagination

#### **[PERF-6]** CSS Performance
- **Flag:** CSS selectors with excessive specificity or nesting (>3 levels)
- **Flag:** `@import` in CSS files (blocks parallel loading)
- **Flag:** Unused CSS not purged in production
- **Flag:** CSS animations using properties that trigger layout (use `transform`/`opacity`)
- **Flag:** Large inline styles on many elements
- **Expect:** Efficient selectors, CSS-in-JS or utility CSS, GPU-accelerated animations

#### **[PERF-7]** JavaScript Execution
- **Flag:** Synchronous heavy computation on main thread
- **Flag:** `JSON.parse()` of very large payloads without streaming
- **Flag:** Blocking `for` loops over large datasets in render
- **Flag:** Missing debouncing/throttling on frequent events (scroll, resize, input)
- **Expect:** Web Workers for heavy computation, `requestAnimationFrame`, debounce/throttle

#### **[PERF-8]** Core Web Vitals
- **Flag:** Largest Contentful Paint (LCP) resources not preloaded
- **Flag:** Cumulative Layout Shift (CLS) caused by dynamic content without reserved space
- **Flag:** Interaction to Next Paint (INP) affected by long tasks
- **Flag:** Render-blocking resources in `<head>` without `async`/`defer`
- **Expect:** `<link rel="preload">` for LCP, skeleton screens, `async`/`defer` on scripts

### 2.3 Minor Performance Issues

- **Flag:** Missing `rel="noopener noreferrer"` on external links with `target="_blank"`
- **Flag:** Fonts loaded without `font-display: swap`
- **Flag:** Missing `<link rel="preconnect">` for known third-party origins
- **Flag:** SVG icons as separate network requests instead of inline or sprite
- **Expect:** Proper link attributes, font loading strategy, resource hints

---

## 3. Code Correctness

### 3.1 Critical Correctness Issues

#### **[CORR-1]** Null/Undefined Reference Issues
- **Flag:** Optional chaining not used for possibly undefined objects
- **Flag:** `null`/`undefined` not handled in data rendering
- **Flag:** Array methods called on possibly `undefined` arrays
- **Flag:** Destructuring without default values on optional data
- **Expect:** Optional chaining (`?.`), nullish coalescing (`??`), proper type guards

#### **[CORR-2]** Async/Promise Handling
- **Flag:** Missing `await` on async function calls
- **Flag:** Unhandled promise rejections (missing `.catch()` or try/catch)
- **Flag:** Race conditions in async state updates
- **Flag:** `async` functions in `useEffect` without proper cleanup
- **Flag:** Promise chains mixing `.then()` and `await` inconsistently
- **Expect:** Consistent async/await, error boundaries, `AbortController` for cancellable requests

#### **[CORR-3]** State Mutation
- **Flag:** Direct mutation of React/Vue state objects
- **Flag:** Array mutations (`push`, `splice`, `sort`) on state arrays
- **Flag:** Object spread missing nested clone for deep objects
- **Flag:** `Object.assign()` used for deep cloning (only shallow)
- **Expect:** Immutable updates, spread operators, `structuredClone()`, Immer for complex state

#### **[CORR-4]** Event Handler Issues
- **Flag:** Event handlers not properly bound (wrong `this` context)
- **Flag:** Missing `event.preventDefault()` on form submissions
- **Flag:** Synthetic event accessed asynchronously in React (event pooling)
- **Flag:** Multiple event listeners attached without deduplication
- **Expect:** Arrow functions or `.bind()`, proper event handling, cleanup on unmount

### 3.2 Major Correctness Issues

#### **[CORR-5]** React Hook Rules
- **Flag:** Hooks called conditionally or inside loops
- **Flag:** Missing dependencies in `useEffect`/`useMemo`/`useCallback` dependency arrays
- **Flag:** Stale closures in event handlers or callbacks
- **Flag:** `useEffect` without cleanup function when needed
- **Flag:** `useState` updater not using function form for derived state
- **Expect:** Hooks at top level, exhaustive dependencies, cleanup functions, ESLint rules of hooks

#### **[CORR-6]** Type Coercion Issues (JavaScript)
- **Flag:** `==` instead of `===` (loose equality)
- **Flag:** Truthy/falsy checks that fail on `0`, `""`, or `false` as valid values
- **Flag:** `parseInt()` without radix parameter
- **Flag:** String to number conversion without validation (`+userInput`)
- **Expect:** Strict equality (`===`), explicit null checks, `Number()` or `parseInt(str, 10)`

#### **[CORR-7]** Browser API Misuse
- **Flag:** `window`/`document` accessed in SSR without guards
- **Flag:** `localStorage` access without try/catch (private browsing)
- **Flag:** Missing feature detection for newer APIs
- **Flag:** Clipboard API used without permission checks
- **Expect:** SSR-safe guards (`typeof window !== 'undefined'`), try/catch for storage, feature detection

#### **[CORR-8]** Date/Time Handling
- **Flag:** `new Date()` string parsing inconsistencies across browsers
- **Flag:** Timezone assumptions in date display
- **Flag:** Date comparison without normalization
- **Flag:** Locale-specific date formatting done manually
- **Expect:** `Intl.DateTimeFormat`, ISO 8601 strings, timezone-aware libraries

---

## 4. Architecture & Design

### 4.1 Critical Architecture Issues

#### **[ARCH-1]** Separation of Concerns
- **Flag:** Business logic in UI components
- **Flag:** API calls directly in components (no service/repository layer)
- **Flag:** Data transformation in rendering code
- **Flag:** Side effects scattered across components
- **Expect:** Custom hooks/composables for logic, service layers, data transformation in utilities

#### **[ARCH-2]** Application Boundaries
- **Flag:** Tight coupling between feature modules
- **Flag:** Shared mutable state between unrelated features
- **Flag:** Circular dependencies between modules
- **Flag:** Missing clear public API for shared modules
- **Expect:** Feature-based module boundaries, explicit exports, loose coupling

### 4.2 Major Architecture Issues

#### **[ARCH-3]** Code Organization Principles
- **Flag:** Components with multiple responsibilities
- **Flag:** God components (>300 lines, multiple concerns)
- **Flag:** Presentation logic mixed with container/data logic
- **Flag:** Utility functions tightly coupled to framework
- **Expect:** Single responsibility, container/presentational split, framework-agnostic utilities

#### **[ARCH-4]** Data Flow
- **Flag:** Prop drilling through many component levels (>3)
- **Flag:** Bidirectional data flow between parent/child
- **Flag:** Global state used for local component state
- **Flag:** Derived state stored separately instead of computed
- **Expect:** Context/providers, unidirectional data flow, computed/derived state, appropriate state scope

---

## 5. Component Design

### 5.1 Critical Component Issues

#### **[COMP-1]** Component Lifecycle
- **Flag:** Side effects in render/template (API calls, subscriptions)
- **Flag:** Missing cleanup on unmount (timers, listeners, subscriptions)
- **Flag:** Infinite render loops (state set in render without condition)
- **Flag:** DOM manipulation outside framework lifecycle
- **Expect:** Side effects in `useEffect`/`onMounted`/lifecycle hooks, proper cleanup

#### **[COMP-2]** Component API Design
- **Flag:** Too many props (>7-10 indicates need for composition)
- **Flag:** Boolean props with unclear naming
- **Flag:** Required props without default values when optional behavior exists
- **Flag:** Props mutated inside child component
- **Expect:** Composition over configuration, clear prop naming, immutable props

### 5.2 Major Component Issues

#### **[COMP-3]** Reusability
- **Flag:** Duplicated component logic across components
- **Flag:** Business logic hardcoded in reusable UI components
- **Flag:** Missing abstraction for repeated patterns
- **Flag:** Tightly coupled components that should be generic
- **Expect:** Custom hooks/composables for shared logic, generic components, composition patterns

#### **[COMP-4]** Component Composition
- **Flag:** Deep component nesting (>5 levels without good reason)
- **Flag:** Missing slot/children patterns for content projection
- **Flag:** Inheritance used instead of composition
- **Flag:** Render props when hooks/composables would be cleaner
- **Expect:** Flat composition, slots/children, composition over inheritance

#### **[COMP-5]** Server Components (Next.js / RSC)
- **Flag:** `"use client"` directive on components that don't need it
- **Flag:** Client components importing server-only modules
- **Flag:** Large props passed from server to client components (serialization overhead)
- **Flag:** Missing `Suspense` boundaries for streaming
- **Expect:** Server components by default, minimal client components, proper boundaries

### 5.3 Minor Component Issues

- **Flag:** Missing `displayName` for HOCs or `forwardRef` components (React)
- **Flag:** Inline function definitions in JSX creating new references each render
- **Flag:** Missing prop documentation/comments for complex components
- **Expect:** Named components, stable references, documented APIs

---

## 6. State Management

### 6.1 Critical State Issues

#### **[STATE-1]** State Architecture
- **Flag:** Mutable state updates (direct object/array mutation)
- **Flag:** State shape that makes updates overly complex
- **Flag:** Sensitive data (tokens, passwords) in client-side state
- **Flag:** Infinite update loops (state change triggers another state change)
- **Expect:** Immutable updates, normalized state, sensitive data in `httpOnly` cookies only

#### **[STATE-2]** Global State Misuse
- **Flag:** All state in global store (Redux, Zustand, Pinia) when local state suffices
- **Flag:** UI-only state (modals, tooltips) in global store
- **Flag:** Form state in global store (unless shared across routes)
- **Flag:** Derived data stored in state instead of computed
- **Expect:** Local state for local concerns, global state for shared data, selectors for derived data

### 6.2 Major State Issues

#### **[STATE-3]** State Synchronization
- **Flag:** Server state duplicated in client state without sync strategy
- **Flag:** Missing optimistic updates for better UX
- **Flag:** Stale state not invalidated after mutations
- **Flag:** Manual cache invalidation when data-fetching libraries handle it
- **Expect:** React Query/SWR/TanStack Query for server state, optimistic updates, cache invalidation

#### **[STATE-4]** Redux / Zustand / Pinia Patterns
- **Flag:** Side effects in reducers (API calls, DOM manipulation)
- **Flag:** Large flat action types without namespacing
- **Flag:** Missing action creators / action type constants
- **Flag:** State accessed without selectors (tight coupling)
- **Flag:** Non-serializable values in state (functions, class instances)
- **Expect:** Pure reducers, middleware for side effects, selectors, serializable state

### 6.3 Minor State Issues

- **Flag:** Missing Redux DevTools / state debugging setup in development
- **Flag:** State not normalized for relational data
- **Flag:** Missing TypeScript types for state shape
- **Expect:** DevTools configured, normalized state for entities, typed state

---

## 7. API Integration & Data Fetching

### 7.1 Critical Data Fetching Issues

#### **[FETCH-1]** Error Handling
- **Flag:** Missing error handling on `fetch`/`axios` calls
- **Flag:** Network errors not communicated to users
- **Flag:** Silent failures on critical API calls
- **Flag:** Error state not cleared on retry
- **Expect:** Try/catch, error boundaries, user-facing error messages, retry logic

#### **[FETCH-2]** Request Management
- **Flag:** API calls without `AbortController` for cancellation
- **Flag:** Race conditions from rapid sequential requests
- **Flag:** Missing loading states during data fetching
- **Flag:** Requests fired on every render without deduplication
- **Expect:** Request cancellation, race condition handling, loading/error/success states

### 7.2 Major Data Fetching Issues

#### **[FETCH-3]** Caching & Revalidation
- **Flag:** Manual caching implementation when React Query/SWR available
- **Flag:** Stale data shown without revalidation strategy
- **Flag:** Missing cache invalidation after mutations
- **Flag:** Refetching data on every component mount
- **Expect:** Data-fetching libraries, stale-while-revalidate, mutation-triggered invalidation

#### **[FETCH-4]** API Client Design
- **Flag:** `fetch`/`axios` calls scattered across components
- **Flag:** Base URL hardcoded in multiple places
- **Flag:** Missing request/response interceptors for auth tokens
- **Flag:** Missing retry logic for transient failures
- **Flag:** Inconsistent error response handling
- **Expect:** Centralized API client, interceptors, typed API functions, consistent error handling

#### **[FETCH-5]** GraphQL (when applicable)
- **Flag:** Over-fetching with queries requesting unnecessary fields
- **Flag:** Missing fragment collocation with components
- **Flag:** N+1 queries from nested resolvers
- **Flag:** Missing query caching
- **Expect:** Minimal field selection, collocated fragments, DataLoader for batching, cache policies

### 7.3 Minor Data Fetching Issues

- **Flag:** Missing request timeout configuration
- **Flag:** API types manually maintained instead of generated (OpenAPI, GraphQL codegen)
- **Flag:** Missing response transformation layer
- **Expect:** Generated types, timeout configuration, response mapping

---

## 8. Forms & Validation

### 8.1 Critical Form Issues

#### **[FORM-1]** Security
- **Flag:** Form data submitted without sanitization
- **Flag:** Missing CSRF tokens on form submissions
- **Flag:** Autocomplete enabled on password/sensitive fields inappropriately
- **Flag:** Form action URL user-controllable (open redirect)
- **Expect:** Input sanitization, CSRF tokens, appropriate `autocomplete` attributes

### 8.2 Major Form Issues

#### **[FORM-2]** Validation
- **Flag:** Client-side only validation (no server-side)
- **Flag:** Missing real-time validation feedback
- **Flag:** Validation errors not associated with specific fields
- **Flag:** Custom validation reimplementing standard HTML5 constraints
- **Flag:** Missing form-level (cross-field) validation
- **Expect:** Server-side validation always, inline field errors, form libraries (React Hook Form, Formik, VeeValidate)

#### **[FORM-3]** State Management
- **Flag:** Controlled components without `onChange` handlers
- **Flag:** Form state in global store when local state suffices
- **Flag:** Missing dirty/touched tracking for user feedback
- **Flag:** Re-rendering entire form on single field change
- **Expect:** Form libraries for complex forms, local state, field-level re-rendering

#### **[FORM-4]** Accessibility
- **Flag:** Form inputs without associated `<label>` elements
- **Flag:** Error messages not programmatically associated (`aria-describedby`)
- **Flag:** Missing `required` attribute on required fields
- **Flag:** Custom form controls without ARIA roles
- **Expect:** Proper labels, `aria-describedby` for errors, semantic HTML, ARIA for custom controls

### 8.3 Minor Form Issues

- **Flag:** Missing `inputMode` for mobile keyboards (`inputMode="numeric"`)
- **Flag:** Missing `autocomplete` hints for browser autofill
- **Flag:** Submit button without `type="submit"`
- **Expect:** Mobile-optimized inputs, proper `autocomplete`, explicit button types

---

## 9. Routing & Navigation

### 9.1 Critical Routing Issues

#### **[ROUTE-1]** Security
- **Flag:** Route-based authorization only on client-side (no server-side)
- **Flag:** Sensitive routes accessible without authentication check
- **Flag:** Route parameters used in API calls without validation
- **Expect:** Server-side auth checks, route guards, parameter validation

### 9.2 Major Routing Issues

#### **[ROUTE-2]** Route Design
- **Flag:** Missing 404/catch-all route handler
- **Flag:** Query parameters not validated or typed
- **Flag:** Route changes not scrolling to top when expected
- **Flag:** Missing loading states during route transitions
- **Flag:** History stack manipulation breaking browser back button
- **Expect:** Error pages, typed params, scroll restoration, loading indicators

#### **[ROUTE-3]** Code Splitting
- **Flag:** All routes in main bundle (no lazy loading)
- **Flag:** Missing `Suspense` fallback for lazy-loaded routes
- **Flag:** Prefetching not configured for likely navigation targets
- **Expect:** `React.lazy()` / dynamic `import()`, Suspense boundaries, link prefetching

### 9.3 Minor Routing Issues

- **Flag:** Hardcoded route paths (use constants or enum)
- **Flag:** Route names not following consistent naming convention
- **Flag:** Missing breadcrumb support for deep navigation
- **Expect:** Route constants, consistent naming, navigation context

---

## 10. Styling & CSS

### 10.1 Critical CSS Issues

#### **[CSS-1]** Security
- **Flag:** User input in CSS `url()`, `expression()`, or `calc()`
- **Flag:** CSS injection via dynamic style attributes with user input
- **Expect:** Sanitized CSS values, no user input in style properties

### 10.2 Major CSS Issues

#### **[CSS-2]** Layout & Responsiveness
- **Flag:** Fixed pixel widths causing horizontal scroll on mobile
- **Flag:** Missing responsive design for primary breakpoints
- **Flag:** `!important` overuse (indicates specificity problems)
- **Flag:** Magic numbers in CSS without comments
- **Flag:** Missing container queries when component-level responsiveness needed
- **Expect:** Fluid layouts, CSS Grid/Flexbox, design tokens/variables, responsive images

#### **[CSS-3]** Consistency & Maintainability
- **Flag:** Inconsistent spacing/sizing (not using design tokens or scale)
- **Flag:** Deeply nested selectors (>3 levels in SCSS/Less)
- **Flag:** Duplicated style blocks across components
- **Flag:** Global styles that could leak into components
- **Flag:** Inline styles for complex styling (except dynamic values)
- **Expect:** CSS variables/design tokens, component-scoped styles, shared utility classes

#### **[CSS-4]** CSS Architecture
- **Flag:** Conflicting global and component styles
- **Flag:** Unmaintainable specificity chains
- **Flag:** Missing CSS reset or normalize
- **Flag:** z-index wars (arbitrary z-index values without system)
- **Expect:** CSS Modules, styled-components, Tailwind, or BEM methodology; z-index scale

#### **[CSS-5]** Dark Mode / Theming
- **Flag:** Hardcoded colors instead of CSS variables/tokens
- **Flag:** Missing `prefers-color-scheme` media query support
- **Flag:** Theme switching causing flash of unstyled content (FOUC)
- **Expect:** CSS custom properties for theming, system preference detection, theme persistence

### 10.3 Minor CSS Issues

- **Flag:** Vendor prefixes manually added (use Autoprefixer)
- **Flag:** Missing `box-sizing: border-box` on root
- **Flag:** Using `px` for font sizes instead of `rem`/`em`
- **Flag:** Missing `print` styles for printable pages
- **Expect:** Autoprefixer, consistent box model, relative units, print styles

---

## 11. Accessibility (a11y)

### 11.1 Critical Accessibility Issues

#### **[A11Y-1]** Keyboard Navigation
- **Flag:** Interactive elements not focusable or operable via keyboard
- **Flag:** Focus trap missing in modals/dialogs
- **Flag:** Focus not returned to trigger element after modal close
- **Flag:** Custom components missing keyboard event handlers
- **Flag:** `tabindex` values > 0 (disrupts natural tab order)
- **Expect:** All interactions keyboard-accessible, proper focus management, `tabindex="0"` or `-1`

#### **[A11Y-2]** Screen Reader Support
- **Flag:** Images without `alt` text (or empty `alt` for decorative images)
- **Flag:** Icon-only buttons without accessible labels (`aria-label`)
- **Flag:** Dynamic content changes not announced (`aria-live`)
- **Flag:** Custom components without appropriate ARIA roles
- **Flag:** `aria-hidden="true"` on interactive/content elements
- **Expect:** Descriptive alt text, `aria-label` / `aria-labelledby`, live regions, proper roles

#### **[A11Y-3]** Semantic HTML
- **Flag:** `<div>` or `<span>` used for buttons, links, or interactive elements
- **Flag:** Missing heading hierarchy (`<h1>` to `<h6>` in order)
- **Flag:** Lists not using `<ul>`/`<ol>`/`<li>`
- **Flag:** Tables used for layout instead of `<div>` with CSS Grid/Flexbox
- **Flag:** Missing `<main>`, `<nav>`, `<header>`, `<footer>` landmarks
- **Expect:** Native HTML elements, proper heading levels, semantic landmarks

### 11.2 Major Accessibility Issues

#### **[A11Y-4]** Color & Contrast
- **Flag:** Text color contrast ratio below WCAG AA (4.5:1 normal, 3:1 large)
- **Flag:** Color as the only means of conveying information
- **Flag:** Interactive elements without visible focus indicator
- **Expect:** Sufficient contrast, multiple visual cues, visible focus styles

#### **[A11Y-5]** Form Accessibility
- **Flag:** Inputs without `<label>` elements
- **Flag:** Error messages not programmatically linked to inputs
- **Flag:** Required fields not indicated (visually and programmatically)
- **Flag:** Form instructions only conveyed visually
- **Expect:** Associated labels, `aria-describedby` for errors, `aria-required`, clear instructions

#### **[A11Y-6]** Motion & Animation
- **Flag:** Animations without `prefers-reduced-motion` media query respect
- **Flag:** Auto-playing media without pause/stop control
- **Flag:** Content that flashes more than 3 times per second
- **Expect:** `prefers-reduced-motion` support, media controls, no seizure-triggering content

### 11.3 Minor Accessibility Issues

- **Flag:** Missing `lang` attribute on `<html>` element
- **Flag:** Missing skip navigation link
- **Flag:** Touch targets smaller than 44x44 CSS pixels
- **Expect:** Language declaration, skip links, adequate touch targets

---

## 12. Internationalization (i18n)

### 12.1 Major i18n Issues

#### **[I18N-1]** Text & Content
- **Flag:** Hardcoded user-facing strings (not in translation files)
- **Flag:** String concatenation for translations (prevents proper pluralization)
- **Flag:** Date/number formatting without `Intl` API or i18n library
- **Flag:** Hardcoded locale or language assumptions
- **Expect:** i18n library (`react-intl`, `i18next`, `vue-i18n`), ICU message format, `Intl` API

#### **[I18N-2]** Layout & Direction
- **Flag:** Fixed widths that break with longer translations
- **Flag:** Missing RTL (right-to-left) support when required
- **Flag:** Icons or images with culturally specific meaning
- **Expect:** Flexible layouts, logical CSS properties (`margin-inline-start`), culturally neutral design

### 12.2 Minor i18n Issues

- **Flag:** Missing plural forms for countable items
- **Flag:** Locale not derived from user preferences or URL
- **Flag:** Missing fallback locale configuration
- **Expect:** Proper pluralization, locale detection, fallback chains

---

## 13. Build & Bundling

### 13.1 Critical Build Issues

#### **[BUILD-1]** Security
- **Flag:** Source maps shipped to production
- **Flag:** Environment secrets baked into client bundle
- **Flag:** Build scripts executing arbitrary code from untrusted sources
- **Expect:** No source maps in prod, build-time env injection, trusted build pipeline

### 13.2 Major Build Issues

#### **[BUILD-2]** Bundle Optimization
- **Flag:** Development mode deployed to production (React, Vue dev mode)
- **Flag:** Missing tree-shaking configuration
- **Flag:** Duplicate dependencies in bundle
- **Flag:** Missing compression (gzip/brotli) in production
- **Flag:** Missing chunk splitting strategy
- **Expect:** Production builds, tree shaking, deduplication, compression, chunk optimization

#### **[BUILD-3]** Build Configuration
- **Flag:** Missing TypeScript strict mode (`strict: true`)
- **Flag:** Build warnings treated as non-blocking
- **Flag:** Missing linting in CI/CD pipeline
- **Flag:** Inconsistent Node.js version across environments
- **Expect:** Strict TypeScript, warnings-as-errors in CI, linting, `.nvmrc` / `engines` field

#### **[BUILD-4]** Asset Optimization
- **Flag:** Unoptimized images in build output
- **Flag:** Missing font subsetting
- **Flag:** CSS not minified in production
- **Flag:** Missing cache-busting file hashes
- **Expect:** Image optimization pipeline, font subsetting, CSS minification, content hashes

### 13.3 Minor Build Issues

- **Flag:** Slow build times without analysis
- **Flag:** Missing bundle analyzer in development workflow
- **Flag:** Build output not gitignored
- **Expect:** Build performance monitoring, bundle analysis, clean git

---

## 14. Testing

### 14.1 Unit Testing

#### **[TEST-1]** Critical Issues
- **Flag:** Tests with no assertions
- **Flag:** Tests that always pass
- **Flag:** Tests relying on implementation details (CSS class names, DOM structure)
- **Flag:** Tests calling production APIs
- **Expect:** Meaningful assertions, behavior-focused testing, mocked APIs

#### **[TEST-2]** Major Issues
- **Flag:** Missing test coverage for critical user flows
- **Flag:** Snapshot tests used as primary testing strategy (brittle)
- **Flag:** Testing internal state instead of rendered output/behavior
- **Flag:** Missing edge case coverage (empty states, error states, loading states)
- **Flag:** `act()` warnings in React tests (missing async handling)
- **Expect:** Testing Library queries (`getByRole`, `getByText`), user-centric tests, async test patterns

#### **[TEST-3]** Minor Issues
- **Flag:** Non-descriptive test names
- **Flag:** Duplicate test setup (use `beforeEach`, shared utilities)
- **Flag:** Missing test for accessibility (e.g., `jest-axe`)
- **Expect:** Descriptive test names, shared fixtures, a11y testing

### 14.2 Integration Testing

#### **[TEST-4]** Major Issues
- **Flag:** Integration tests without API mocking (MSW, nock)
- **Flag:** Tests depending on specific DOM structure instead of accessible queries
- **Flag:** Missing route transition tests
- **Flag:** Missing form submission flow tests
- **Expect:** MSW for API mocking, accessible queries, user journey tests

### 14.3 End-to-End Testing

#### **[TEST-5]** Major Issues
- **Flag:** Brittle selectors (data-testid overuse, CSS class selectors)
- **Flag:** Missing wait strategies (flaky tests)
- **Flag:** No test data cleanup
- **Flag:** E2E tests coupled to specific environment data
- **Expect:** Stable selectors (text, role), proper waits, test data factories, environment-agnostic

### 14.4 Visual Regression Testing

#### **[TEST-6]** Minor Issues
- **Flag:** Missing visual regression tests for design-critical components
- **Flag:** Storybook stories without interaction tests
- **Expect:** Chromatic/Percy for visual regression, Storybook play functions

---

## 15. Error Handling & Observability

### 15.1 Critical Issues

#### **[ERR-1]** Error Boundaries
- **Flag:** Missing error boundaries around route-level components (React)
- **Flag:** Unhandled JavaScript errors crashing entire application
- **Flag:** Error UI not providing recovery options (retry, navigate home)
- **Flag:** Errors silently swallowed in catch blocks
- **Expect:** Error boundaries, fallback UI, recovery actions, error logging

#### **[ERR-2]** Error Reporting
- **Flag:** No error monitoring service (Sentry, Datadog, etc.)
- **Flag:** PII/sensitive data in error reports
- **Flag:** Missing source maps for error stacktrace resolution
- **Flag:** `console.error` as sole error reporting in production
- **Expect:** Error monitoring service, data scrubbing, private source maps, structured error reporting

### 15.2 Major Issues

#### **[ERR-3]** User-Facing Errors
- **Flag:** Technical error messages shown to users (stack traces, error codes)
- **Flag:** Missing error states for network failures
- **Flag:** No offline/connectivity indicator
- **Flag:** Missing loading timeout with error feedback
- **Expect:** User-friendly error messages, offline handling, timeout feedback

#### **[ERR-4]** Logging
- **Flag:** `console.log` / `console.debug` in production code
- **Flag:** Excessive logging impacting performance
- **Flag:** Missing structured logging format
- **Expect:** Proper log levels, tree-shakeable logging, structured format

### 15.3 Minor Issues

- **Flag:** Missing performance monitoring (Web Vitals reporting)
- **Flag:** No user session replay for debugging
- **Expect:** RUM (Real User Monitoring), session recording for production debugging

---

## 16. HTML & Semantic Markup

### 16.1 Critical HTML Issues

#### **[HTML-1]** Security
- **Flag:** Missing `<!DOCTYPE html>` (quirks mode security issues)
- **Flag:** Forms with `action` pointing to external untrusted URLs
- **Flag:** Iframes without `sandbox` attribute for untrusted content
- **Expect:** DOCTYPE declaration, validated form actions, sandboxed iframes

### 16.2 Major HTML Issues

#### **[HTML-2]** Semantics
- **Flag:** Non-semantic markup (`<div>` soup)
- **Flag:** Incorrect heading hierarchy (skipping levels)
- **Flag:** Interactive elements nested improperly (`<a>` inside `<button>`)
- **Flag:** Missing `<meta charset="utf-8">`
- **Flag:** Missing `<meta name="viewport">` for responsive design
- **Expect:** Semantic HTML5 elements, proper heading order, correct nesting, required meta tags

#### **[HTML-3]** SEO (when applicable)
- **Flag:** Missing `<title>` or duplicate titles across pages
- **Flag:** Missing meta description
- **Flag:** Images without `alt` text
- **Flag:** Non-descriptive link text ("click here")
- **Flag:** Missing Open Graph / Twitter Card meta tags
- **Expect:** Unique titles, meta descriptions, descriptive alt text, descriptive link text, social meta

### 16.3 Minor HTML Issues

- **Flag:** Deprecated HTML attributes (`align`, `border`, `bgcolor`)
- **Flag:** Unnecessary `<br>` for spacing (use CSS)
- **Flag:** IDs not unique on page
- **Expect:** Modern HTML, CSS for layout, unique IDs

---

## 17. TypeScript Usage

### 17.1 Critical TypeScript Issues

#### **[TS-1]** Type Safety
- **Flag:** `any` type used broadly (especially for API responses, state, props)
- **Flag:** Type assertions (`as`) bypassing type checks without justification
- **Flag:** `@ts-ignore` / `@ts-expect-error` without explanation
- **Flag:** `!` (non-null assertion) on potentially null values without guard
- **Expect:** Proper types, type guards, discriminated unions, `unknown` instead of `any`

### 17.2 Major TypeScript Issues

#### **[TS-2]** Type Design
- **Flag:** Overly broad types that don't constrain values
- **Flag:** Missing discriminated unions for state machines (loading/error/success)
- **Flag:** `interface` vs `type` inconsistency within project
- **Flag:** Missing generic constraints
- **Flag:** String literal types not used for known value sets
- **Expect:** Precise types, discriminated unions, consistent type definitions, constrained generics

#### **[TS-3]** Type Organization
- **Flag:** Types defined in component files (should be separate for reuse)
- **Flag:** Duplicate type definitions across files
- **Flag:** Missing generated types for API contracts
- **Flag:** `enum` used where union type or `as const` suffices
- **Expect:** Shared type files, generated API types, `as const` objects over enums

#### **[TS-4]** Strict Mode
- **Flag:** `strict: false` or individual strict options disabled in `tsconfig.json`
- **Flag:** `noUncheckedIndexedAccess` not enabled
- **Flag:** Implicit `any` parameters in functions
- **Expect:** Full strict mode, `noUncheckedIndexedAccess`, explicit types

### 17.3 Minor TypeScript Issues

- **Flag:** Missing return types on exported functions
- **Flag:** Utility types not used when applicable (`Partial`, `Pick`, `Omit`, `Record`)
- **Flag:** Missing JSDoc on complex types
- **Expect:** Explicit return types on public APIs, utility type usage, documented complex types

---

## 18. Dependency Management

### 18.1 Critical Issues

- **Flag:** Packages with known vulnerabilities (`npm audit`)
- **Flag:** Packages executing scripts on install without review
- **Flag:** Missing lock file (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
- **Flag:** Dependencies fetched from non-registry sources without verification
- **Expect:** Regular audits, lock files committed, verified sources

### 18.2 Major Issues

- **Flag:** Outdated packages with security patches
- **Flag:** Duplicate dependencies (different versions of same package)
- **Flag:** `devDependencies` shipped in production bundle
- **Flag:** Unnecessary dependencies (reimplementing simple utilities)
- **Flag:** Missing `engines` field in `package.json` for Node version
- **Flag:** Framework-specific packages version mismatches (React 17 package in React 18 project)
- **Expect:** Regular updates, deduplication, minimal dependencies, version alignment

### 18.3 Minor Issues

- **Flag:** Not using workspace features for monorepos
- **Flag:** Inconsistent package manager usage in team (npm vs yarn vs pnpm)
- **Flag:** Missing `overrides`/`resolutions` for transitive vulnerability fixes
- **Expect:** Consistent package manager, workspace configuration, override strategies

---

## 19. Project & Code Structure

### 19.1 Project Structure

#### **[PROJ-1]** Expected Structure (Feature-Based)
```
src/
├── app/                        # App-level setup (routing, providers, layout)
│   ├── routes/                 # Route definitions
│   ├── providers/              # Global context providers
│   └── layout/                 # App shell, navigation
├── features/                   # Feature modules
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/             # (or composables/)
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── index.ts           # Public API
│   ├── dashboard/
│   └── settings/
├── shared/                     # Shared/common code
│   ├── components/            # Reusable UI components
│   ├── hooks/                 # Shared hooks/composables
│   ├── services/              # API client, utilities
│   ├── types/                 # Shared TypeScript types
│   ├── utils/                 # Pure utility functions
│   └── constants/
├── assets/                     # Static assets (images, fonts)
├── styles/                     # Global styles, themes, tokens
└── test/                       # Test utilities, setup, factories
    ├── setup.ts
    ├── factories/
    └── mocks/
```

#### **[PROJ-2]** Critical Structure Issues
- **Flag:** No clear separation between features
- **Flag:** Circular dependencies between feature modules
- **Flag:** Business logic in shared/common modules
- **Expect:** Feature-based organization, clear boundaries, barrel exports

#### **[PROJ-3]** Major Structure Issues
- **Flag:** Inconsistent folder structure across features
- **Flag:** Deeply nested directories (>4 levels)
- **Flag:** Tests mixed with source code without convention
- **Flag:** Missing barrel files (`index.ts`) for module public API
- **Expect:** Consistent structure, flat where possible, co-located or mirrored tests

### 19.2 File Organization

#### **[PROJ-4]** Major Issues
- **Flag:** Component file >300 lines (split into smaller components)
- **Flag:** Multiple components per file (without clear relationship)
- **Flag:** Utility file doing too many things
- **Flag:** Missing separation of types/constants from logic
- **Expect:** One component per file, focused utility modules, separated concerns

#### **[PROJ-5]** Minor Issues
- **Flag:** Inconsistent file naming (mixing `camelCase`, `PascalCase`, `kebab-case`)
- **Flag:** Missing consistent file extension convention (`.tsx` vs `.jsx`)
- **Flag:** Test files not co-located or consistently named
- **Expect:** PascalCase for components, camelCase or kebab-case for utilities, consistent extensions

---

## 20. Anti-Patterns to Flag

### Critical Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| XSS via innerHTML | Script injection | Framework templating, DOMPurify |
| Secrets in client code | Credential exposure | Server-side env, BFF pattern |
| Infinite render loops | App freeze/crash | Proper dependency arrays, guards |
| Direct state mutation | Unpredictable UI, lost updates | Immutable updates, Immer |
| eval() with user input | Remote code execution | Safe parsing, AST |

### Major Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Prop drilling (>3 levels) | Coupling, maintenance burden | Context, composition, state management |
| God component | Unmaintainable, untestable | Split by responsibility |
| Derived state in store | Stale data, sync bugs | Selectors, computed values |
| Callback hell | Readability, error handling | async/await, proper composition |
| Layout thrashing | Jank, poor performance | Batch DOM reads/writes |
| CSS !important abuse | Specificity wars | Proper CSS architecture |
| String-based refs | Deprecated, fragile | Callback refs, `useRef` |
| Premature optimization | Unnecessary complexity | Profile first, optimize what matters |
| Over-mocking in tests | Tests don't verify real behavior | Integration tests, MSW |
| Copy-paste components | Duplication, inconsistency | Extract shared components/hooks |

### Minor Anti-Patterns
| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| Comments explaining what | Indicates unclear code | Self-documenting code |
| Commented-out code | Version control exists | Delete it |
| Dead/Unused Code | Clutters the codebase | Remove unused imports, components |
| Console.log in production | Noise, potential data leak | Proper logging service |
| Magic numbers in CSS | Maintenance difficulty | CSS variables, design tokens |
| Div soup | Poor accessibility, SEO | Semantic HTML elements |

---

## 21. Naming & Style Conventions

### Major Issues
- **Flag:** Inconsistent naming conventions within project
- **Flag:** Non-PascalCase component names (React/Vue/Angular)
- **Flag:** Non-camelCase function and variable names
- **Flag:** Non-UPPER_SNAKE_CASE constants
- **Flag:** Generic names (`data`, `info`, `item`, `handler`, `temp`) without context
- **Flag:** Abbreviations that aren't universally understood

### Minor Issues
- **Flag:** Boolean variables/props not using `is`, `has`, `can`, `should` prefixes
- **Flag:** Event handler props not using `on` prefix (`onClick`, `onSubmit`)
- **Flag:** Hook names not starting with `use` (React)
- **Flag:** CSS class naming not following project convention (BEM, Tailwind, CSS Modules)
- **Flag:** Inconsistent file naming convention
- **Flag:** Missing consistent code formatting (Prettier/ESLint not configured)
- **Expect:** Prettier + ESLint configured, consistent naming, clear conventions documented

---

## 22. Modern Features & Best Practices

### Encourage Usage When Applicable
- CSS Container Queries for component-level responsiveness
- CSS `:has()` selector for parent-based styling
- CSS nesting (native, without preprocessor)
- `structuredClone()` for deep cloning
- `AbortController` for request cancellation
- `Intl` API for dates, numbers, pluralization
- `import.meta.env` for environment variables (Vite)
- View Transitions API for smooth page transitions
- `Popover` API and `<dialog>` element for modals
- `loading="lazy"` and `fetchpriority` for resource hints
- `@layer` for CSS cascade management
- Signals-based reactivity (Solid, Angular, Preact signals)

### Flag Legacy Patterns
- **Flag:** jQuery usage in modern frameworks
- **Flag:** `var` declarations (use `const`/`let`)
- **Flag:** `arguments` object (use rest parameters)
- **Flag:** `.bind(this)` in class components when arrow functions or hooks available
- **Flag:** `componentDidMount`/class components when function components with hooks available (React)
- **Flag:** `XMLHttpRequest` when `fetch` available
- **Flag:** CommonJS `require()` in browser code (use ES modules)
- **Flag:** Callbacks when Promises/async-await available
- **Flag:** Moment.js (use `date-fns`, `dayjs`, or `Intl`)
- **Flag:** CSS vendor prefixes manually added (use Autoprefixer)
- **Flag:** `@import` in CSS (use bundler imports)
- **Flag:** `document.querySelector` for framework-managed DOM

---

## Review Checklist Summary

Before approving, verify no issues exist in these categories:

### Must Check (Critical)
- [ ] No XSS vulnerabilities (innerHTML, eval, unsanitized input)
- [ ] No secrets or credentials in client-side code
- [ ] Authentication tokens handled securely (httpOnly cookies)
- [ ] No memory leaks (event listeners, subscriptions cleaned up)
- [ ] No infinite render loops
- [ ] Error boundaries in place
- [ ] Proper null/undefined handling
- [ ] No direct state mutation

### Should Check (Major)
- [ ] Bundle size optimized (code splitting, tree shaking)
- [ ] Core Web Vitals considered (LCP, CLS, INP)
- [ ] Proper async/await and error handling
- [ ] TypeScript used correctly (no `any` abuse)
- [ ] Accessibility standards met (keyboard, screen reader, contrast)
- [ ] Forms properly validated (client and server)
- [ ] API integration has error/loading/empty states
- [ ] Tests cover critical user flows
- [ ] Responsive design for target viewports
- [ ] State management appropriate (local vs global)
- [ ] Data fetching with caching strategy

### Could Check (Minor)
- [ ] Naming follows project conventions
- [ ] Code is readable and well-organized
- [ ] Modern JS/CSS features used appropriately
- [ ] Documentation present for complex components
- [ ] Consistent project structure
- [ ] i18n support where needed
- [ ] Visual regression coverage for critical UI

---

*Last updated: February 2026 | Target: ES2022+, TypeScript 5+, Modern Frameworks*

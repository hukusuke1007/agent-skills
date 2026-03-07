---
name: "flutter-riverpod-arch"
description: "Implement Feature-First architecture with Riverpod state management and Flutter Hooks in Flutter applications"
license: "MIT"
metadata:
  author: "shohei"
  version: "1.0.0"
---

# Flutter Riverpod Architecture

## Goal

Implements scalable Flutter applications using the Feature-First directory structure, Riverpod (with code generation) for state management, and `flutter_hooks` / `HookConsumerWidget` for UI composition. The design philosophy is three layers — presentation, domain, and infrastructure — and the code-level notation in this skill is UI, UseCase, and Repository. Data source access is encapsulated inside repositories. Applies `@Riverpod(keepAlive: true)` for repository providers and `@riverpod` for screen-scoped state.

### Layer Mapping (Source of Truth)

| Design philosophy | Code-level notation |
| --- | --- |
| presentation | UI |
| domain | UseCase |
| infrastructure | Repository |

## Decision Logic

Before implementing, evaluate the following to determine the correct approach:

**Provider scope**

- Does the state need to persist across screen navigations, or is it a repository / auth state shared across features?
  - _Yes_ → Use `@Riverpod(keepAlive: true)`
  - _No_ → Use `@riverpod` (auto-disposed when no longer watched)

**UseCase vs. Repository** (domain/infrastructure mapping)

- Does the operation simply read/write a single data source with no business rules?
  - _Yes_ → Implement in the Repository.
- Does the operation combine repositories, require validation, or orchestrate a multi-step process?
  - _Yes_ → Create a dedicated UseCase.

**Feature vs. Core placement**

- Is the use case/repository implementation used by only one feature?
  - _Yes_ → Place in `features/{feature}/providers/`
  - _No_ → Place in `core/providers/`

**Directory structure policy**

- Default: keep both layers under `providers/` and split by responsibility:
  - `providers/use_cases/` for UseCase/controller implementations
  - `providers/repositories/` for Repository/data access implementations
- Recommended names in this skill are `use_cases` and `repositories`.
- Alternative names (`domain`, `infrastructures`) are also acceptable.

## Instructions

### 1. Plan the Feature Structure

Identify the feature module, the providers required, and the correct layer for each piece of logic.

**STOP AND ASK THE USER:** "Which feature does this belong to? Is the data source a remote API, local database, or both? Does the logic require combining multiple data sources or complex validation that warrants a dedicated Use Case?"

Place code according to this structure:

```
lib/
  core/
    providers/       # Shared UseCase + Repository implementations
    widgets/         # Reusable widgets
    extensions/      # Extension methods
    res/             # Colors, text styles, theme
  features/
    {feature}/
      providers/
        use_cases/      # UseCase, controllers
        repositories/   # Repository, data access
      pages/
        widgets/     # Page-specific widgets
      {feature}_page.dart
```

_Validate-and-Fix:_ Confirm that no UseCase/Repository implementation is placed inside `pages/`. Confirm that shared implementations live in `core/providers/` (or explicit `core/use_cases` / `core/repositories`), not duplicated across features.

---

### 2. Implement the Repository Layer

Create a repository class that encapsulates all access to a single data source (API, local DB). Annotate its provider with `@Riverpod(keepAlive: true)`. After adding annotations, run code generation:

```bash
dart run build_runner build
```

See **[providers.md](references/providers.md)** for the full implementation pattern.

_Validate-and-Fix:_ Confirm the repository contains no business logic (no validation, no multi-source orchestration). Confirm the provider function returns only the repository instance, and that `@Riverpod(keepAlive: true)` is used (not `@riverpod`).

---

### 3. Implement the UseCase Layer

For operations that involve validation, multi-step orchestration, or combining repositories, create a dedicated UseCase class inside `providers/use_cases/` (alternative: `domain/`). Three patterns:

- **Async data fetcher** — `class FetchPosts extends _$FetchPosts` with `Future<T> build()`
- **Action use case (callable class)** — `CreatePost` with `call()` for commands; invalidate dependent providers after writes
- **Stateful controller** — `class PostController extends _$PostController` for screen-scoped UI state

See **[providers.md](references/providers.md)** for full implementation patterns.

_Validate-and-Fix:_ Confirm each use case handles only one responsibility. Confirm that `ref.invalidate()` is called after mutations to keep dependent providers fresh. Confirm `@riverpod` (not `keepAlive`) is used for screen-scoped use cases.

---

### 4. Build the UI with HookConsumerWidget

Extend `HookConsumerWidget` for all stateful pages and complex widgets. Use hooks (`useScrollController`, `useTextEditingController`, etc.) for local UI state. Provide a static `show()` method for type-safe navigation. When using a declarative router (GoRouter, auto_route), replace `show()` with the router's push API.

See **[presentation.md](references/presentation.md)** for page structure and hooks patterns. For mouse cursor requirements on macOS/Web see **[button.md](references/ui/button.md)**.

_Validate-and-Fix:_ Confirm that `ref.watch()` is never called inside event handlers (`onPressed`, `onTap`, etc.). Confirm that `ref.read()` is never called at the top of `build()` to derive reactive state. Confirm `HookConsumerWidget` is used for all stateful pages and complex widgets. Confirm macOS/Web interactive widgets include `enabledMouseCursor` or `mouseCursor`.

---

### 5. Implement Responsive Layout

Use `ResponsiveLayout` for page-level breakpoints based on `MediaQuery.sizeOf(context)`. Treat tablet and macOS as the same layout tier. Use `LayoutBuilder` only for widget-level (not page-level) breakpoints.

See **[responsive.md](references/ui/responsive.md)** for breakpoints, `ResponsiveLayout` implementation, and platform-specific patterns.

_Validate-and-Fix:_ Confirm that `LayoutBuilder` is not used for page-level breakpoint decisions. Confirm that targeted `MediaQuery` static methods (`MediaQuery.sizeOf`, `MediaQuery.paddingOf`, `MediaQuery.orientationOf`) are used instead of `MediaQuery.of(context)` to avoid unnecessary rebuilds.

---

### 6. Write Tests

Use `ProviderContainer` with overrides to test providers and use cases in isolation. Define a `createContainer` helper in `test/utils.dart`. Use `mockito` for mocking external dependencies.

See **[testing.md](references/testing.md)** for full test patterns (repository, use case, controller, widget tests).

_Validate-and-Fix:_ Confirm that every test overrides all external dependencies (API clients, databases). Confirm that `addTearDown(container.dispose)` is called for every `ProviderContainer`. Confirm widget tests use `ProviderScope` with overrides rather than calling real repositories.

---

## Constraints

- **Prefer `HookConsumerWidget`:** This skill uses `HookConsumerWidget` (with `flutter_hooks`) for all stateful pages and complex widgets. `StatefulWidget` may be used for isolated, purely local UI state with no Riverpod interaction.
- **No `ref.read()` in `build`:** `ref.read()` must only appear inside event handlers or callbacks, never at the top of a `build` method to derive reactive UI state.
- **No `ref.watch()` in event handlers:** `ref.watch()` must only appear inside `build()` or a provider's `build()` method.
- **No business logic in Views:** Widget classes must contain only layout, conditional rendering, and navigation. All data transformation and validation must reside in Use Cases or Repositories.
- **No `SingleChildScrollView + Column` for dynamic lists:** Always use `ListView.builder` (or `SliverList` inside `CustomScrollView`) for lists of dynamic length.
- **No button wrapper widgets:** Never create a custom wrapper widget for a single button purpose. Configure appearance via `styleFrom` or a shared `AppButtonStyle` utility class.
- **Use targeted `MediaQuery` static methods:** Prefer `MediaQuery.sizeOf`, `MediaQuery.paddingOf`, `MediaQuery.orientationOf` etc. over `MediaQuery.of(context)` to avoid unnecessary rebuilds.
- **No `LayoutBuilder` for page-level breakpoints:** Use `ResponsiveLayout` (which uses `MediaQuery.sizeOf`) so the layout decision is based on actual screen width, not parent constraints.
- **Mouse cursors required on macOS/Web:** Every `Button` variant must include `enabledMouseCursor: SystemMouseCursors.click`. Every `InkWell` must include `mouseCursor: SystemMouseCursors.click`.
- **Code generation required:** After adding or modifying a `@riverpod` annotation, always run `dart run build_runner build`.
- **Naming conventions:** Files and directories use `snake_case`; classes use `UpperCamelCase`; page classes end in `Page`; repository classes end in `Repository`; use case classes use verb-noun format (e.g., `FetchPosts`, `CreatePost`).

## Reference Files

- **[architecture.md](references/architecture.md)** — Project structure, directory layout, naming conventions
- **[providers.md](references/providers.md)** — Repository and use case implementation patterns
- **[riverpod.md](references/riverpod.md)** — Provider types, `ref.watch` vs `ref.read`, caching, code generation
- **[presentation.md](references/presentation.md)** — Page structure, navigation, hooks usage, error handling
- **[testing.md](references/testing.md)** — Test patterns, mocking strategy, `ProviderContainer` usage
- **[button.md](references/ui/button.md)** — Button patterns, `styleFrom`, hover cursor for macOS/Web
- **[list.md](references/ui/list.md)** — `ListView.builder`, Pull-to-Refresh, pagination with Slivers
- **[responsive.md](references/ui/responsive.md)** — Breakpoints, `ResponsiveLayout`, platform-specific layouts

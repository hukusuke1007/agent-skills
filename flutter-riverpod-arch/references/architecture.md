# Flutter App Architecture

## Overview

- Three-layer design philosophy: Presentation → Domain → Infrastructure
- Code-level notation in this skill: UI → UseCase → Repository
- Data Source is encapsulated inside Infrastructure repositories
- Feature-First directory structure
- Riverpod for state management
- Hooks-based widget composition (`HookConsumerWidget`)

## Project Structure

```
lib/
  core/
    constants/        // App-wide constants
    extensions/       // Extension methods
    providers/        // Shared UseCase + Repository implementations
    res/              // Resources (colors, text styles, theme)
    utils/            // Utility functions
    widgets/          // Shared widgets
  features/
    {feature}/        // One directory per feature
      providers/      // UseCase + Repository for this feature
      pages/
        widgets/      // Page-specific widgets
      {feature}_page.dart
test/
  unit/
  widget/
```

### The `providers/` Directory (Default)

Manage both UseCase and Repository implementations inside `providers/` by default.
Split by responsibility.

**Flat layout (few files):**

```
features/post/providers/
  use_cases/
    fetch_posts.dart
    create_post.dart
    delete_post.dart
  repositories/
    post_repository.dart
```

**Detailed layout (many files):**

```
features/post/providers/
  use_cases/
    fetch_posts.dart
    create_post.dart
    delete_post.dart
    post_controller.dart    // UI-facing state controller
  repositories/
    post_repository.dart
    post_remote_data_source.dart
```

**`core/providers/` (shared across features):**

```
core/providers/
  auth/
    use_cases/
      sign_in.dart
      sign_out.dart
    repositories/
      auth_repository.dart
  storage/
    repositories/
      preferences_repository.dart
```

### Conceptual Layer Names

If `providers` is unclear for your team, you may explain the same concepts with explicit layer names instead. The recommended actual directory names in this skill remain `use_cases` and `repositories`.

```
features/post/
  use_cases/           // conceptually: domain
    fetch_posts.dart
    create_post.dart
  repositories/        // conceptually: infrastructures
    post_repository.dart
```

## State Management Guidelines

1. Use Riverpod with `@riverpod` annotations and code generation.
2. Let `riverpod_generator` determine the correct `Notifier` class.
3. Use appropriate local storage:
   - Simple flags and settings → `SharedPreferences`
   - Complex user data or content → `sembast`, `sqflite`, etc.
4. Use immutable state patterns.

## Widget Guidelines

1. Use `HookConsumerWidget` for all stateful pages and complex widgets. `StatefulWidget` may be used for isolated, purely local UI state with no Riverpod interaction.
2. Implement error handling with user-friendly messages and retry actions.
3. Follow Material 3 design principles.
4. Navigation pattern:
   - Implement a static `show()` method on each page for type-safe navigation.
   - Use `Navigator.push` with `CupertinoPageRoute` (iOS-style) or `MaterialPageRoute` (adaptive) for transitions. When using GoRouter or auto_route, replace `static show()` with the router's push API.
   - Define `routeName` as a static getter on each page class.

## Provider Guidelines

1. Design philosophy: `Presentation + Domain + Infrastructure`.
2. Code-level notation: `UI + UseCase + Repository`.
3. UseCase provides application logic that satisfies business requirements.
4. Repository provides data persistence and retrieval functionality, including API, database, and local storage operations.
5. Default layout: place UseCase/Repository implementations in `features/{feature}/providers/` and `core/providers/`.
6. Optional explanation terms: `Domain` and `Infrastructures` may be used as conceptual layer names, while actual directory names remain `use_cases` and `repositories`.
7. Keep each file focused on a single responsibility.
8. Implement error handling in every async provider.

## Feature Organization

1. Organize by feature first; technology layer second.
2. Keep features independent — cross-feature dependencies flow through `core/`.
3. Share common code via `core/` (widgets, providers, extensions).
4. Follow consistent naming patterns throughout.

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Directories / Files | `snake_case` | `post_repository.dart` |
| Classes | `UpperCamelCase` | `PostRepository` |
| Variables / Functions | `camelCase` | `fetchPosts` |
| Constants | `camelCase` | `kMaxRetries` |
| Pages | `NounPage` | `PostListPage`, `PostDetailPage` |
| UI Components | `NounComponentType` | `PostListTile`, `PostCard` |
| Repositories | `NounRepository` | `PostRepository` |
| Use Cases | `VerbNoun` | `FetchPosts`, `CreatePost`, `DeletePost` |
| Controllers | `NounController` | `PostController` |

## Performance Guidelines

1. Cache images appropriately.
2. Optimize list views:
   - Use `ListView.builder` for lazy loading.
   - Implement pagination for large data sets.
   - Handle loading and error states explicitly.
3. Avoid unnecessary provider rebuilds by splitting providers appropriately.

## Model Layer

Model / domain classes (e.g., `Post`, `User`) should follow the same architectural conventions as the rest of the project. Prefer immutable models with `fromJson` / `toJson`. Recommended approaches are `freezed`, or hand-written immutable classes combined with `equatable`. Choose the approach that best fits the project and keep the model style consistent across the codebase.

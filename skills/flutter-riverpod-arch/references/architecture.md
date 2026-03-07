# Flutter App Architecture

## Overview

- Four-layer architecture: UI → Use Case → Repository → Data Source
- Feature-First directory structure
- Riverpod for state management
- Hooks-based widget composition (`HookConsumerWidget`)

## Project Structure

```
lib/
  core/
    constants/        // App-wide constants
    extensions/       // Extension methods
    providers/        // Shared providers and repositories
    res/              // Resources (colors, text styles, theme)
    utils/            // Utility functions
    widgets/          // Shared widgets
  features/
    {feature}/        // One directory per feature
      providers/      // Business logic and repositories for this feature
      pages/
        widgets/      // Page-specific widgets
      {feature}_page.dart
test/
  unit/
  widget/
```

### The `providers/` Directory

Both business logic (use cases) and repository implementations live inside `providers/`.
Use subdirectories when the file count grows.

**Flat layout (few files):**

```
features/post/providers/
  post_repository.dart
  fetch_posts.dart
  create_post.dart
  delete_post.dart
```

**Subdirectory layout (many files):**

```
features/post/providers/
  repositories/
    post_repository.dart
  use_cases/
    fetch_posts.dart
    create_post.dart
    delete_post.dart
  post_controller.dart    // UI-facing state controller
```

**`core/providers/` (shared across features):**

```
core/providers/
  auth/
    auth_repository.dart
    sign_in.dart
    sign_out.dart
  storage/
    preferences_repository.dart
```

## State Management Guidelines

1. Use Riverpod with `@riverpod` annotations and code generation.
2. Let `riverpod_generator` determine the correct `Notifier` class.
3. Use appropriate local storage:
   - Simple flags and settings → `SharedPreferences`
   - Complex user data or content → `sembast`, `sqflite`, etc.
4. Use immutable state patterns.
5. Choose the correct provider scope (see Decision Logic in SKILL.md).

## Widget Guidelines

1. Use `HookConsumerWidget` for all stateful pages and complex widgets. `StatefulWidget` may be used for isolated, purely local UI state with no Riverpod interaction.
2. Implement error handling with user-friendly messages and retry actions.
3. Follow Material 3 design principles.
4. Navigation pattern:
   - Implement a static `show()` method on each page for type-safe navigation.
   - Use `Navigator.push` with `CupertinoPageRoute` (iOS-style) or `MaterialPageRoute` (adaptive) for transitions. When using GoRouter or auto_route, replace `static show()` with the router's push API.
   - Define `routeName` as a static getter on each page class.

## Provider Guidelines

1. Place providers in `features/{feature}/providers/` (feature-specific) or `core/providers/` (shared).
2. Use subdirectories when `providers/` contains more than ~5 files.
3. Implement error handling in every async provider.
4. Follow the single-responsibility principle: one provider manages one piece of state.

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
| Providers (generated) | `nounProvider` | `postRepositoryProvider`, `fetchPostsProvider` |

## Performance Guidelines

1. Cache images appropriately.
2. Optimize list views:
   - Use `ListView.builder` for lazy loading.
   - Implement pagination for large data sets.
   - Handle loading and error states explicitly.
3. Avoid unnecessary provider rebuilds by splitting providers appropriately.

## Model Layer (Out of Scope)

Model / domain classes (e.g., `Post`, `User`) are outside the scope of this skill. By convention, use immutable value objects with `fromJson` / `toJson`. Implementation options include hand-written classes with `copyWith`, `freezed`, or `dart_mappable`. Choose whichever fits the project.

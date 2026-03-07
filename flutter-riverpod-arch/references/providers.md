# Provider Directory: Code Design and Implementation Rules

## 1. Architecture Layers

```
UI Layer          →  HookConsumerWidget, pages, widgets
Use Case Layer    →  Business logic inside provider classes
Repository Layer  →  Data source abstraction
Data Source Layer →  API clients, local databases
```

Data flows strictly downward: UI → Use Case → Repository → Data Source.

## 2. Directory Structure

```
lib/
├── core/providers/         # Shared across features
│   ├── auth/
│   │   ├── auth_repository.dart
│   │   └── sign_in.dart
│   └── storage/
│       └── preferences_repository.dart
├── features/
│   ├── post/
│   │   ├── providers/      # Post-specific logic
│   │   │   ├── post_repository.dart
│   │   │   ├── fetch_posts.dart
│   │   │   └── create_post.dart
│   │   └── pages/
│   └── ...
```

## 3. Repository Implementation

A repository encapsulates access to a single data source. It must contain no business logic.

### Definition

```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'post_repository.g.dart';

@Riverpod(keepAlive: true)
PostRepository postRepository(Ref ref) => PostRepository(ApiClient());

class PostRepository {
  PostRepository(this._apiClient);
  final ApiClient _apiClient;

  Future<List<Post>> fetchPosts() async {
    final response = await _apiClient.get('/posts');
    return (response as List).map(Post.fromJson).toList();
  }

  Future<Post> fetchPost(String id) async {
    return Post.fromJson(await _apiClient.get('/posts/$id'));
  }

  Future<void> createPost(Post post) =>
      _apiClient.post('/posts', body: post.toJson());

  Future<void> deletePost(String id) => _apiClient.delete('/posts/$id');
}
```

### Rules

1. **Single responsibility:** One repository per domain or data source.
2. **Encapsulation:** Hide API/DB details from business logic.
3. **Return types:** Return domain models (or `List<T>`), not raw API responses.
4. **Always `keepAlive: true`:** Repository providers must persist for the app's lifetime.

## 4. Use Case Implementation

Use cases implement application-specific operations. Create a use case when the operation involves validation, multi-step logic, or combining repositories.

### Class-based (async data)

```dart
part 'fetch_posts.g.dart';

@riverpod
class FetchPosts extends _$FetchPosts {
  @override
  Future<List<Post>> build() =>
      ref.watch(postRepositoryProvider).fetchPosts();
}
```

### Function-based (action / command)

```dart
part 'create_post.g.dart';

@riverpod
CreatePost createPost(Ref ref) => CreatePost(ref);

class CreatePost {
  CreatePost(this._ref);
  final Ref _ref;

  Future<void> call({required String title, required String body}) async {
    if (title.trim().isEmpty) {
      throw AppException(message: 'Title is required.');
    }
    await _ref.read(postRepositoryProvider).createPost(
          Post(title: title, body: body),
        );
    _ref.invalidate(fetchPostsProvider);
  }
}
```

> `AppException` is a project-specific typed exception class. Replace with your own exception type or the standard Dart `Exception`.

### Stateful controller

```dart
part 'post_controller.g.dart';

@riverpod
class PostController extends _$PostController {
  @override
  PostState build() => PostState.initial();

  Future<void> save(Post post) async {
    state = state.copyWith(isSaving: true);
    try {
      await ref.read(createPostProvider).call(
            title: post.title,
            body: post.body,
          );
      state = state.copyWith(isSaving: false, isSuccess: true);
    } on AppException catch (e) {
      state = state.copyWith(isSaving: false, errorMessage: e.message);
    }
  }
}
```

> `PostState` is a project-specific immutable state class. Replace with your own state class, or use `AsyncValue<T>` for async state.

### Naming conventions

| Type                | Class name       | Example                    |
| ------------------- | ---------------- | -------------------------- |
| Repository          | `NounRepository` | `PostRepository`           |
| Async data fetcher  | `VerbNoun`       | `FetchPosts`, `FetchPost`  |
| Action use case     | `VerbNoun`       | `CreatePost`, `DeletePost` |
| UI state controller | `NounController` | `PostController`           |

### Rules

1. **Single responsibility:** One use case per operation.
2. **Inject via Riverpod:** Use `ref.read(repositoryProvider)` inside use cases; never instantiate repositories directly.
3. **Invalidate after mutations:** Call `ref.invalidate(provider)` after writes so dependent providers stay fresh.
4. **Scope correctly:** Use `@riverpod` (auto-disposed) for screen-scoped use cases and controllers.

## 5. Code Generation

```dart
// Required in every file that uses @riverpod or @Riverpod
part 'my_provider.g.dart';
```

```bash
# Generate once
dart run build_runner build

# Watch for changes
dart run build_runner watch
```

## 6. Module Dependencies

```
UI Layer
  ↓
Use Case Layer
  ↓
Repository Layer
  ↓
Data Source Layer
```

- Upper layers depend on lower layers; never the reverse.
- Avoid circular dependencies between providers.

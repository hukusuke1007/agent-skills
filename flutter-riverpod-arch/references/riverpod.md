# Riverpod Implementation Guidelines

## 1. Provider Scope

### Persistent (`@Riverpod(keepAlive: true)`)

Use for state that must survive for the entire app lifetime:

- Repositories (data source access)
- Stateless command providers (action entry points)
- Authentication state
- Global app settings
- Shared caches

```dart
@Riverpod(keepAlive: true)
UserRepository userRepository(Ref ref) => UserRepository(ApiClient());
```

### Auto-disposed (`@riverpod`)

Use for state scoped to a screen or a short-lived operation:

- Screen-specific state
- Form state
- UI controllers
- Async fetchers tied to UI lifecycle

```dart
@riverpod
class PostController extends _$PostController {
  @override
  PostState build() => PostState.initial();
}
```

## 2. Naming Conventions

| Type             | Class suffix | Generated provider name  |
| ---------------- | ------------ | ------------------------ |
| State controller | `Controller` | `postControllerProvider` |
| Repository       | `Repository` | `postRepositoryProvider` |
| Async fetcher    | `VerbNoun`   | `fetchPostsProvider`     |

## 3. State Patterns

### Async data

```dart
@riverpod
class FetchPosts extends _$FetchPosts {
  @override
  Future<List<Post>> build() =>
      ref.watch(postRepositoryProvider).fetchPosts();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(postRepositoryProvider).fetchPosts(),
    );
  }
}

// Consuming in UI
final postsAsync = ref.watch(fetchPostsProvider);
postsAsync.when(
  data: (posts) => ListView.builder(/* ... */),
  loading: () => const CircularProgressIndicator(),
  error: (e, _) => Text('Error: $e'),
);
```

### Synchronous state (local storage integration)

```dart
@riverpod
class ThemeModeController extends _$ThemeModeController {
  @override
  ThemeMode build() {
    final prefs = ref.watch(sharedPreferencesProvider);
    return ThemeMode.values.byName(
      prefs.getString('themeMode') ?? 'system',
    );
  }

  void setThemeMode(ThemeMode mode) {
    state = mode;
    ref.read(sharedPreferencesProvider).setString('themeMode', mode.name);
  }
}
```

## 4. Error Handling

```dart
// Using AsyncValue.guard
Future<void> refresh() async {
  state = const AsyncValue.loading();
  state = await AsyncValue.guard(
    () => ref.read(postRepositoryProvider).fetchPosts(),
  );
}

// Manual try/catch
Future<void> save(Post post) async {
  try {
    state = state.copyWith(isSaving: true);
    await ref.read(postRepositoryProvider).createPost(post);
    state = state.copyWith(isSaving: false, isSuccess: true);
  } on Exception catch (e) {
    state = state.copyWith(isSaving: false, errorMessage: e.toString());
  }
}
```

## 5. Cache Invalidation

```dart
// Invalidate one provider
ref.invalidate(fetchPostsProvider);

// Invalidate multiple providers
ref
  ..invalidate(fetchPostsProvider)
  ..invalidate(fetchUserProvider);

// Update existing cache without refetching
state = state.whenData((list) => [...list, newItem]);
```

## 6. `ref.watch` vs `ref.read`

This is the most common source of bugs. Follow this rule strictly:

| Location                              | Method        | Reason                                  |
| ------------------------------------- | ------------- | --------------------------------------- |
| `build()` method (widget or provider) | `ref.watch()` | Subscribes; rebuilds when state changes |
| Event handler / callback              | `ref.read()`  | One-time read; does not subscribe       |

```dart
// CORRECT
@override
Widget build(BuildContext context, WidgetRef ref) {
  final posts = ref.watch(fetchPostsProvider); // ✓ reactive
  return ListView(/* ... */);
}

void onAddPressed(WidgetRef ref) {
  ref.read(postControllerProvider.notifier).save(post); // ✓ one-time action
}

// INCORRECT
@override
Widget build(BuildContext context, WidgetRef ref) {
  final posts = ref.read(fetchPostsProvider); // ✗ will not react to changes
  return ListView(/* ... */);
}
```

Also valid: calling `ref.read()` on a provider obtained via `ref.watch()` in `build`:

```dart
final notifier = ref.watch(postControllerProvider.notifier);
// notifier is obtained reactively; calling notifier.save() is fine
```

## 7. Code Generation Setup

```yaml
# pubspec.yaml — check pub.dev for latest versions
dependencies:
  flutter_riverpod:
  riverpod_annotation:
  hooks_riverpod:
  flutter_hooks:

dev_dependencies:
  riverpod_generator:
  build_runner:
```

Every file using `@riverpod` or `@Riverpod` must include the `part` directive:

```dart
part 'my_provider.g.dart';
```

```bash
dart run build_runner build   # one-time
dart run build_runner watch   # continuous
```

## 8. Best Practices

- **Default rule:** Use `@riverpod` for screen-scoped/stateful providers, and `@Riverpod(keepAlive: true)` for repositories plus stateless command providers.
- **Split providers** to minimize rebuild scope; one provider per piece of state.
- **Avoid circular dependencies** between providers.
- **Use `ref.invalidate()`** after mutations to keep dependent providers consistent.

## Official Documentation

For package setup, latest installation guidance, and the official introduction flow, refer to Riverpod's Getting Started guide:
[https://riverpod.dev/docs/introduction/getting_started](https://riverpod.dev/docs/introduction/getting_started)

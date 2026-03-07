# Flutter Testing Guidelines

## Directory Structure

```
test/
├── features/           # Feature-specific tests
├── core/               # Core utility tests
└── utils.dart          # Shared test utilities (createContainer, etc.)
```

## Test Utility

Define a `createContainer` helper in `test/utils.dart`:

```dart
ProviderContainer createContainer({
  ProviderContainer? parent,
  List<Override> overrides = const [],
  List<ProviderObserver>? observers,
}) {
  final container = ProviderContainer(
    parent: parent,
    overrides: overrides,
    observers: observers,
  );
  addTearDown(container.dispose);
  return container;
}
```

## 1. Repository Tests

Mock the data source (API client, database) using `mockito`. Test both success and error cases.

```dart
@GenerateNiceMocks([MockSpec<ApiClient>()])
void main() {
  group('PostRepository', () {
    late MockApiClient mockClient;
    late PostRepository repository;

    setUp(() {
      mockClient = MockApiClient();
      repository = PostRepository(mockClient);
    });

    test('fetchPosts returns a list of posts', () async {
      when(mockClient.get('/posts')).thenAnswer(
        (_) async => [{'id': '1', 'title': 'Hello'}],
      );
      final posts = await repository.fetchPosts();
      expect(posts, hasLength(1));
      expect(posts.first.title, 'Hello');
    });

    test('fetchPosts propagates exception on network error', () async {
      when(mockClient.get('/posts')).thenThrow(Exception('Network error'));
      expect(() => repository.fetchPosts(), throwsException);
    });
  });
}
```

Generate mocks after adding `@GenerateNiceMocks`:

```bash
dart run build_runner build
```

## 2. Use Case / Provider Tests

Use `ProviderContainer` with repository overrides to test use cases in isolation.

```dart
void main() {
  group('FetchPosts', () {
    test('returns posts from repository', () async {
      final container = createContainer(
        overrides: [
          postRepositoryProvider.overrideWith(
            (ref) => FakePostRepository(),
          ),
        ],
      );
      final posts = await container.read(fetchPostsProvider.future);
      expect(posts, isNotEmpty);
    });

    test('exposes error state when repository throws', () async {
      final container = createContainer(
        overrides: [
          postRepositoryProvider.overrideWith(
            (ref) => FailingPostRepository(),
          ),
        ],
      );
      final state = await container.read(fetchPostsProvider.future).then(
            (_) => null,
            onError: (e) => e,
          );
      expect(state, isA<Exception>());
    });
  });
}
```

## 3. Controller / Notifier Tests

Test state transitions by listening to the notifier.

```dart
void main() {
  test('PostController.save updates state correctly', () async {
    final container = createContainer(
      overrides: [
        postRepositoryProvider.overrideWith((ref) => FakePostRepository()),
      ],
    );

    final notifier = container.read(postControllerProvider.notifier);

    await notifier.save(Post(title: 'Test', body: 'Body'));

    final state = container.read(postControllerProvider);
    expect(state.isSuccess, isTrue);
    expect(state.isSaving, isFalse);
  });
}
```

## 4. Widget Tests

Use `ProviderScope` with overrides to inject fake dependencies.

```dart
void main() {
  testWidgets('PostListPage shows loading indicator initially', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          fetchPostsProvider.overrideWith(
            (ref) => Future.delayed(const Duration(seconds: 1), () => []),
          ),
        ],
        child: const MaterialApp(home: PostListPage()),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('PostListPage shows list when data loads', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          fetchPostsProvider.overrideWith(
            (ref) async => [Post(id: '1', title: 'Hello', body: 'World')],
          ),
        ],
        child: const MaterialApp(home: PostListPage()),
      ),
    );

    await tester.pump(); // trigger async
    expect(find.text('Hello'), findsOneWidget);
  });
}
```

## 5. Fake Implementations

Prefer `Fake` classes over `Mock` for simple predictable behavior:

```dart
class FakePostRepository implements PostRepository {
  final _posts = [Post(id: '1', title: 'Fake Post', body: 'Body')];

  @override
  Future<List<Post>> fetchPosts() async => _posts;

  @override
  Future<Post> fetchPost(String id) async =>
      _posts.firstWhere((p) => p.id == id);

  @override
  Future<void> createPost(Post post) async => _posts.add(post);

  @override
  Future<void> deletePost(String id) async =>
      _posts.removeWhere((p) => p.id == id);
}
```

## Best Practices

- **Every external dependency must be overridden.** Never let a test call a real API or database.
- **Always call `addTearDown(container.dispose)`** (handled by `createContainer`).
- **Group tests by class:** `group('PostRepository', () { ... })`.
- **Describe behavior, not implementation:** `test('returns empty list when no posts exist', ...)`.
- **Test both success and error paths** for every async operation.
- **Widget tests use `ProviderScope` overrides**, not `ProviderContainer`.

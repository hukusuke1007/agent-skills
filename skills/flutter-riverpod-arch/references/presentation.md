# Presentation Layer Implementation

## Directory Structure

```
lib/
├── features/
│   └── {feature}/
│       ├── pages/
│       │   ├── {page}_page.dart
│       │   └── widgets/
│       │       └── {widget}.dart
├── core/
│   ├── widgets/        # Shared widgets
│   ├── extensions/     # BuildContext extensions
│   └── res/            # Theme, colors, text styles
```

## Page Structure

This skill uses `HookConsumerWidget` for all pages to enable both Riverpod (`ref`) and `flutter_hooks` in a single widget. `StatefulWidget` may be used for isolated, purely local UI state with no Riverpod interaction. Provide a static `show()` method for type-safe navigation.

```dart
class PostListPage extends HookConsumerWidget {
  const PostListPage({super.key});

  static String get routeName => 'post_list';

  static Future<void> show(BuildContext context) =>
      Navigator.of(context, rootNavigator: true).push<void>(
        CupertinoPageRoute(
          settings: RouteSettings(name: routeName),
          builder: (_) => const PostListPage(),
        ),
      );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsAsync = ref.watch(fetchPostsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Posts')),
      body: postsAsync.when(
        data: (posts) => PostListView(posts: posts),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorMessage(
          message: e.toString(),
          onRetry: () => ref.invalidate(fetchPostsProvider),
        ),
      ),
    );
  }
}
```

> **Navigation options:** `CupertinoPageRoute` provides iOS-style slide transitions. Use `MaterialPageRoute` for platform-adaptive animations. When using a declarative router (GoRouter, auto_route), replace `static show()` with the router's push API.

## Flutter Hooks Usage

Use `flutter_hooks` for local UI state (scroll controllers, focus nodes, animation controllers). Do not use hooks for state that needs to be shared across widgets — use Riverpod for that.

```dart
@override
Widget build(BuildContext context, WidgetRef ref) {
  final scrollController = useScrollController();
  final searchController = useTextEditingController();
  final focusNode = useFocusNode();

  // Run once on mount
  useEffect(() {
    // Initialization logic
    return null; // return a cleanup function or null
  }, const []);

  return Scaffold(/* ... */);
}
```

## State Management in UI

```dart
// Reactive state — ref.watch() in build
final postsAsync = ref.watch(fetchPostsProvider);

// Async data rendering
postsAsync.when(
  data: (posts) => ListView.builder(
    itemCount: posts.length,
    itemBuilder: (context, index) => PostListTile(post: posts[index]),
  ),
  loading: () => const Center(child: CircularProgressIndicator()),
  error: (e, _) => ErrorMessage(
    message: e.toString(),
    onRetry: () => ref.invalidate(fetchPostsProvider),
  ),
);

// Event handler — ref.read() only
FilledButton(
  onPressed: () => ref.read(postControllerProvider.notifier).save(post),
  child: const Text('Save'),
);
```

## Error Handling

```dart
class ErrorMessage extends StatelessWidget {
  const ErrorMessage({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(message),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
        ],
      ),
    );
  }
}
```

## Responsive Layout

For page-level breakpoints use `ResponsiveLayout`.
See [responsive.md](ui/responsive.md) for full details.

```dart
ResponsiveLayout(
  smallBuilder: (context) => const MobilePage(),
  largeBuilder: (context) => const DesktopPage(),
);
```

## Widget Decomposition

```dart
// Page-specific widgets → features/{feature}/pages/widgets/
class PostListTile extends StatelessWidget {
  const PostListTile({super.key, required this.post, this.onTap});
  final Post post;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(post.title, style: Theme.of(context).textTheme.bodyMedium),
      subtitle: Text(post.body, style: Theme.of(context).textTheme.bodySmall),
      onTap: onTap,
    );
  }
}

// Shared widgets → core/widgets/
class ErrorMessage extends StatelessWidget { /* ... */ }
```

## Design Guidelines

1. **Naming:** Pages end in `Page`; components use descriptive noun+type names (e.g., `PostListTile`, not `PostWidget`).
2. **Performance:** Avoid unnecessary rebuilds; use `ListView.builder` for all dynamic lists.
3. **Accessibility:** Ensure sufficient tap area (minimum 44×44 dp); provide semantic labels.
4. **Error recovery:** Always provide a retry action for async failures.

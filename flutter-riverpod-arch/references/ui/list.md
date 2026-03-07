# Flutter List Implementation

## Overview

Always use `ListView.builder` for dynamic lists. For Pull-to-Refresh and infinite scroll pagination, use `CustomScrollView` with Slivers.

## Basic `ListView.builder`

```dart
class PostListPage extends HookConsumerWidget {
  const PostListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsAsync = ref.watch(fetchPostsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Posts')),
      body: postsAsync.when(
        data: (posts) => ListView.builder(
          itemCount: posts.length,
          itemBuilder: (context, index) => PostListTile(
            post: posts[index],
            onTap: () => PostDetailPage.show(context, posts[index].id),
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
```

## Pull-to-Refresh and Pagination

### `PullToRefresh` component

Encapsulates pull-to-refresh and infinite scroll pagination.

```dart
class PullToRefresh extends HookWidget {
  const PullToRefresh({
    super.key,
    required this.slivers,
    this.onRefresh,
    this.onLoadMore,
    this.onLoadMoreStart,
    this.onLoadMoreEnd,
    this.enableRefresh = true,
    this.enablePagination = true,
    this.controller,
    this.physics,
    this.paginationIndicator,
  });

  final List<Widget> slivers;
  final Future<void> Function()? onRefresh;
  final Future<void> Function()? onLoadMore;
  final Future<void> Function()? onLoadMoreStart;
  final Future<void> Function()? onLoadMoreEnd;
  final bool enableRefresh;
  final bool enablePagination;
  final ScrollController? controller;
  final ScrollPhysics? physics;
  final Widget? paginationIndicator;

  @override
  Widget build(BuildContext context) {
    final isLoadingMore = useState(false);

    Future<void> handleLoadMore() async {
      if (!enablePagination || isLoadingMore.value) return;
      isLoadingMore.value = true;
      try {
        await onLoadMoreStart?.call();
        await onLoadMore?.call();
        await onLoadMoreEnd?.call();
      } finally {
        if (context.mounted) isLoadingMore.value = false;
      }
    }

    return NotificationListener<ScrollUpdateNotification>(
      onNotification: (notification) {
        final m = notification.metrics;
        if (m.maxScrollExtent > 0 && m.extentAfter == 0) {
          Future<void>(handleLoadMore);
        }
        return false;
      },
      child: CustomScrollView(
        controller: controller,
        physics: physics ??
            const BouncingScrollPhysics(
              parent: AlwaysScrollableScrollPhysics(),
            ),
        slivers: [
          if (enableRefresh)
            CupertinoSliverRefreshControl(onRefresh: onRefresh),
          ...slivers,
          if (enablePagination)
            SliverToBoxAdapter(
              child: Visibility(
                visible: isLoadingMore.value,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: paginationIndicator ??
                      const Center(child: CircularProgressIndicator()),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
```

> **Cross-platform note:** `CupertinoSliverRefreshControl` provides iOS-style pull-to-refresh. For Material-style refresh on all platforms, wrap a `CustomScrollView` with `RefreshIndicator` instead:
> ```dart
> RefreshIndicator(
>   onRefresh: onRefresh,
>   child: CustomScrollView(slivers: [...slivers]),
> )
> ```

### Usage

```dart
class PostListPage extends HookConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsAsync = ref.watch(fetchPostsProvider);
    final posts = postsAsync.value ?? [];

    return Scaffold(
      body: PullToRefresh(
        onRefresh: () async => ref.invalidate(fetchPostsProvider),
        onLoadMore: () async =>
            ref.read(fetchPostsProvider.notifier).fetchMore(),
        slivers: [
          SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) => PostListTile(post: posts[index]),
              childCount: posts.length,
            ),
          ),
        ],
      ),
    );
  }
}
```

## Sliver Types

### `SliverList`

```dart
SliverList(
  delegate: SliverChildBuilderDelegate(
    (context, index) => PostListTile(post: items[index]),
    childCount: items.length,
  ),
);
```

### `SliverGrid`

```dart
SliverGrid(
  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
    crossAxisCount: 3, // adjust based on MediaQuery.sizeOf(context).shortestSide
    mainAxisSpacing: 4,
    crossAxisSpacing: 4,
  ),
  delegate: SliverChildBuilderDelegate(
    (context, index) => ItemCard(item: items[index]),
    childCount: items.length,
  ),
);
```

### `SliverToBoxAdapter` — mixed content

```dart
CustomScrollView(
  slivers: [
    SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text('Featured', style: Theme.of(context).textTheme.headlineMedium),
      ),
    ),
    SliverGrid(/* grid content */),
    SliverToBoxAdapter(
      child: Text('Recent', style: Theme.of(context).textTheme.headlineMedium),
    ),
    SliverList(/* list content */),
  ],
);
```

## Best Practices

1. **`ListView.builder` for all dynamic lists.** Never use `SingleChildScrollView + Column` for lists of unknown length.
2. **Use `SliverList` / `SliverGrid` inside `CustomScrollView`** when combining multiple scrollable sections or implementing Pull-to-Refresh.
3. **Responsive grid column counts:** Base `crossAxisCount` on `MediaQuery.sizeOf(context).shortestSide`.
4. **Prevent duplicate load requests:** Gate on `isLoadingMore.value` before triggering pagination.
5. **Check `context.mounted`** before updating state after any async operation.

## Rules

- `SliverList` and `SliverGrid` can only be used inside `CustomScrollView`.
- For static content (known at build time), `ListView` without a builder is acceptable.
- When using `CupertinoSliverRefreshControl`, it must be placed as the first sliver in `CustomScrollView`. When using `RefreshIndicator`, wrap the entire `CustomScrollView` instead.

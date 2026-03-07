# Flutter Responsive Layout

## Overview

For apps targeting iOS, Android, macOS, and Web, implement layout switching based on screen size and platform using consistent patterns.

## Breakpoints

| Tier            | Condition             | Layout                               |
| --------------- | --------------------- | ------------------------------------ |
| Phone           | `shortestSide < 600`  | `BottomNavigationBar`, single-column |
| Tablet / macOS  | `shortestSide >= 600` | Side menu, two-column layout         |
| Compact sidebar | `width <= 1000`       | Switch side menu to `Drawer`         |

## `ResponsiveLayout` Widget

Use `ResponsiveLayout` for page-level layout switching. It uses `MediaQuery.sizeOf(context).width` — actual screen width — not `LayoutBuilder` constraints, which reflect only the parent widget's size.

```dart
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.smallBuilder,
    required this.largeBuilder,
    this.largeScreenMinWidth = 600,
  });

  final Widget Function(BuildContext context) smallBuilder;
  final Widget Function(BuildContext context) largeBuilder;
  final double largeScreenMinWidth;

  @override
  Widget build(BuildContext context) {
    final isLarge =
        MediaQuery.sizeOf(context).width >= largeScreenMinWidth;
    return isLarge ? largeBuilder(context) : smallBuilder(context);
  }
}
```

### Usage

```dart
ResponsiveLayout(
  smallBuilder: (context) => Scaffold(
    body: bodyContent,
    bottomNavigationBar: const AppBottomNavigationBar(),
  ),
  largeBuilder: (context) => Scaffold(
    body: Row(
      children: [
        const AppSideMenuBar(),
        const VerticalDivider(width: 1),
        Expanded(child: bodyContent),
      ],
    ),
  ),
);
```

Custom threshold:

```dart
ResponsiveLayout(
  largeScreenMinWidth: 800,
  smallBuilder: (_) => const MobilePage(),
  largeBuilder: (_) => const DesktopPage(),
);
```

> **Do not** use `LayoutBuilder` for page-level breakpoint decisions.
> `LayoutBuilder` constraints represent the parent widget's size, which may differ from screen width.
> Use `ResponsiveLayout` (which uses `MediaQuery.sizeOf`) instead.

## Platform-Specific Layout Switching

Treat tablet and macOS as the same layout tier:

```dart
import 'dart:io';

// Inside build():
final isTablet = MediaQuery.sizeOf(context).shortestSide >= 600;
final page = (Platform.isMacOS || isTablet)
    ? const HomeDesktopPage()
    : const HomeMobilePage();
```

For platform-specific system operations (file I/O, etc.) in the logic layer, use `dart:io`:

```dart
import 'dart:io';
if (Platform.isMacOS) { /* macOS file export */ }
```

For Web, use `kIsWeb` from `package:flutter/foundation.dart` (`Platform` is not available on Web):

```dart
import 'package:flutter/foundation.dart';
if (kIsWeb) { /* web-specific logic */ }
```

## Sidebar / Drawer Pattern

Show a persistent side menu on tablet/macOS; switch to a `Drawer` when `width <= 1000`.

```dart
final isCompact = MediaQuery.sizeOf(context).width <= 1000;

Scaffold(
  drawer: isCompact
      ? Drawer(
          child: AppSideMenuBar(
            onSelected: (index) {
              onSelected(index);
              Navigator.of(context).pop();
            },
          ),
        )
      : null,
  body: Row(
    children: [
      if (!isCompact) ...[
        AppSideMenuBar(onSelected: onSelected),
        const VerticalDivider(width: 1),
      ],
      Expanded(child: bodyContent),
    ],
  ),
);
```

## Responsive Padding and Grid

```dart
final width = MediaQuery.sizeOf(context).width;
final isTablet = MediaQuery.sizeOf(context).shortestSide >= 600;
final isLandscape = MediaQuery.orientationOf(context) == Orientation.landscape;

// Horizontal content padding
final horizontalPadding = isTablet ? width * 0.15 : (isLandscape ? width * 0.1 : 24.0);
Padding(
  padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
  child: content,
);

// Grid with responsive column count
final crossAxisCount = isTablet ? (isLandscape ? 9 : 7) : (isLandscape ? 5 : 3);
GridView.builder(
  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
    crossAxisCount: crossAxisCount,
    crossAxisSpacing: 4,
    mainAxisSpacing: 4,
  ),
  itemBuilder: (context, index) => ItemCard(item: items[index]),
  itemCount: items.length,
);
```

## `LayoutBuilder` for Sub-Widget Breakpoints

Use `LayoutBuilder` only for widget-level (not page-level) size adaptations:

```dart
LayoutBuilder(
  builder: (context, constraints) {
    return constraints.maxWidth >= 400
        ? const WideVariant()
        : const NarrowVariant();
  },
);
```

## Best Practices

1. Use targeted `MediaQuery` static methods (`MediaQuery.sizeOf`, `MediaQuery.paddingOf`, `MediaQuery.orientationOf`) instead of `MediaQuery.of(context)` to avoid unnecessary rebuilds.
2. Use `ResponsiveLayout` for page-level layout switching; use `LayoutBuilder` for widget-level adaptations only.
3. Treat tablet and macOS as the same layout tier to minimize code duplication.
4. Use `Platform.isMacOS` for macOS checks in both UI and logic layers. Use `kIsWeb` (from `package:flutter/foundation.dart`) for web-specific logic, as `Platform` is unavailable on Web.

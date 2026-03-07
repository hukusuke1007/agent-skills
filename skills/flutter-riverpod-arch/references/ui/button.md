# Flutter Button Implementation

## Overview

Use Material button components (`FilledButton`, `OutlinedButton`, `TextButton`). Configure appearance via `styleFrom` or a shared `AppButtonStyle` utility class. Never create a wrapper widget for a single button purpose.

## macOS / Web: Mouse Cursor (Required)

On macOS and Web, interactive widgets require an explicit cursor. Omitting it results in the default arrow cursor, which degrades UX.

### Button widgets

Always include `enabledMouseCursor: SystemMouseCursors.click` via `styleFrom`:

```dart
FilledButton(
  style: FilledButton.styleFrom(
    enabledMouseCursor: SystemMouseCursors.click,
  ),
  onPressed: () {},
  child: const Text('Submit'),
);
```

### InkWell

```dart
InkWell(
  mouseCursor: SystemMouseCursors.click,
  onTap: () {},
  child: const Text('Tappable text'),
);
```

### GestureDetector

`GestureDetector` has no cursor property. Wrap with `MouseRegion` or replace with `InkWell`:

```dart
MouseRegion(
  cursor: SystemMouseCursors.click,
  child: GestureDetector(
    onTap: () {},
    child: const Text('Clickable'),
  ),
);
```

---

## Pattern 1: Inline `styleFrom`

Use for one-off styles that are not reused elsewhere.

```dart
FilledButton(
  style: FilledButton.styleFrom(
    minimumSize: const Size(double.infinity, 56),
    enabledMouseCursor: SystemMouseCursors.click,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
  ),
  onPressed: () {},
  child: const Text('Submit'),
);
```

## Pattern 2: Shared `AppButtonStyle` Class

Use for styles reused across multiple screens.

```dart
// core/res/app_button_style.dart
class AppButtonStyle {
  AppButtonStyle._();

  static ButtonStyle primary(
    BuildContext context, {
    Size minimumSize = const Size(double.infinity, 56),
    BorderRadius? borderRadius,
  }) =>
      FilledButton.styleFrom(
        minimumSize: minimumSize,
        enabledMouseCursor: SystemMouseCursors.click,
        shape: RoundedRectangleBorder(
          borderRadius: borderRadius ?? BorderRadius.circular(12),
        ),
        textStyle: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold),
      );

  static ButtonStyle secondary(BuildContext context) =>
      OutlinedButton.styleFrom(
        enabledMouseCursor: SystemMouseCursors.click,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      );

  static ButtonStyle destructive(BuildContext context) =>
      FilledButton.styleFrom(
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
        enabledMouseCursor: SystemMouseCursors.click,
      );
}

// Usage
FilledButton(
  style: AppButtonStyle.primary(context),
  onPressed: () {},
  child: const Text('Save'),
);
```

---

## Button Types

### FilledButton — primary action

```dart
FilledButton(
  style: FilledButton.styleFrom(
    minimumSize: const Size(double.infinity, 56),
    enabledMouseCursor: SystemMouseCursors.click,
  ),
  onPressed: () {},
  child: const Text('Submit'),
);
```

### OutlinedButton — secondary action

```dart
OutlinedButton(
  style: OutlinedButton.styleFrom(
    minimumSize: const Size(double.infinity, 56),
    enabledMouseCursor: SystemMouseCursors.click,
    side: const BorderSide(color: Colors.blue),
  ),
  onPressed: () {},
  child: const Text('Cancel'),
);
```

### TextButton — low-emphasis action

```dart
TextButton(
  style: TextButton.styleFrom(
    enabledMouseCursor: SystemMouseCursors.click,
  ),
  onPressed: () {},
  child: const Text('Skip'),
);
```

---

## Button State Management

### Disabled state

```dart
FilledButton(
  onPressed: isEnabled ? () {} : null, // null = disabled
  child: const Text('Submit'),
);
```

### Loading state

```dart
class SubmitButton extends HookWidget {
  const SubmitButton({super.key, required this.onSubmit});
  final Future<void> Function() onSubmit;

  @override
  Widget build(BuildContext context) {
    final isLoading = useState(false);

    Future<void> handlePress() async {
      isLoading.value = true;
      try {
        await onSubmit();
      } finally {
        isLoading.value = false;
      }
    }

    return FilledButton(
      style: FilledButton.styleFrom(
        minimumSize: const Size(double.infinity, 56),
        enabledMouseCursor: SystemMouseCursors.click,
      ),
      onPressed: isLoading.value ? null : handlePress,
      child: isLoading.value
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Text('Submit'),
    );
  }
}
```

---

## Best Practices

1. **No wrapper widgets:** Never create a widget whose sole purpose is wrapping a button with a fixed style.
2. **Mouse cursor always set:** Every button must include `enabledMouseCursor: SystemMouseCursors.click` for macOS/Web.
3. **Disable during loading:** Set `onPressed: null` while async work is in progress to prevent double submission.
4. **Choose the correct type:** `FilledButton` for primary actions, `OutlinedButton` for secondary, `TextButton` for low-emphasis.
5. **Minimum tap area:** Ensure at least 44×44 dp for accessibility.

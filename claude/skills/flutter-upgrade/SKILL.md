---
name: flutter-upgrade
description: Flutter upgrade workflow. Use when upgrading Flutter SDK and dependencies.
argument-hint: <target version>
---

# Flutter Upgrade Workflow

Please upgrade Flutter and all dependencies following best practices:

1. **Pre-upgrade checks**:
   - Run `flutter pub outdated` to see what will be upgraded
   - Check for major version upgrades and research breaking changes
   - Ensure git working tree is clean

2. **Upgrade Flutter SDK**:
   ```bash
   flutter upgrade
   ```

3. **Upgrade dependencies**:
   ```bash
   flutter pub upgrade --major-versions
   ```

4. **Regenerate code** (if using code generation):
   ```bash
   make generate  # or flutter pub run build_runner build --delete-conflicting-outputs
   ```

5. **Run quality gates**:
   ```bash
   flutter analyze
   dart run custom_lint  # if using Riverpod/custom linters
   make test  # or flutter test
   ```

6. **Apply automated fixes** (if analyzer suggests migrations):
   ```bash
   dart fix --apply
   ```

7. **Manual testing**:
   - Test critical user flows
   - Test on both platforms if applicable
   - Pay special attention to areas affected by major version upgrades

8. **Document breaking changes**:
   - Note any code changes required
   - Update team on migration steps if needed

For major version upgrades, always:
- Check package changelogs for breaking changes
- Search for migration guides: "[package-name] [old-version] to [new-version] migration"
- Test thoroughly before committing

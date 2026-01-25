# React Native Upgrade Command

You are tasked with upgrading a React Native application to version $1 (or the latest version if not specified).

## Task Overview

Perform a React Native upgrade following best practices and using the official upgrade diff from react-native-community/rn-diff-purge.

## Instructions

1. **Determine versions:**
   - Check the current React Native version in package.json
   - If $1 is not specified, search for the latest React Native version online
   - The target version is: ${1:-latest}

2. **Research and validate:**
   - Search online for the latest React Native release notes
   - Check for any critical breaking changes or migration requirements
   - Verify New Architecture compatibility requirements for the target version

3. **Fetch the upgrade diff:**
   - Construct the diff URL: `https://raw.githubusercontent.com/react-native-community/rn-diff-purge/diffs/diffs/[current]..${1}.diff`
   - Fetch and analyze the diff to understand all required changes

4. **Check dependency compatibility:**
   - Identify all third-party native modules in package.json
   - Research New Architecture compatibility for critical dependencies:
     - Firebase packages (@react-native-firebase/*)
     - Navigation libraries (@react-navigation/*)
     - UI libraries (react-native-reanimated, react-native-gesture-handler, etc.)
     - Custom native modules
   - Flag any incompatible libraries and recommend alternatives or updates

5. **Plan the upgrade:**
   - Create a comprehensive todo list with TodoWrite tool
   - Break down into phases:
     - Dependency updates (package.json)
     - Android native code changes (MainApplication, Gradle, gradle.properties)
     - iOS native code changes (AppDelegate, Podfile, Info.plist, .pbxproj)
     - Handle library-specific migrations
     - Install dependencies and pods
   - Use ExitPlanMode to present the plan to the user for approval

6. **Execute the upgrade:**
   - Update package.json with new React Native and React versions
   - Update all @react-native/* packages to match the target version
   - Apply native code changes from the diff, preserving:
     - Custom package names/bundle identifiers
     - Third-party SDK integrations (e.g., Firebase, analytics, crash reporting)
     - Custom build configurations
     - Existing native modules
   - Update Gradle wrapper if required by the diff
   - Enable/configure New Architecture if required
   - Install dependencies: yarn install
   - Install iOS pods: cd ios && pod install

7. **Important considerations:**
   - ALWAYS preserve custom native code integrations
   - Replace template package names (e.g., com.helloworld) with actual package names
   - Check for react-native-fast-image compatibility (may need @d11/react-native-fast-image fork)
   - Update related dependencies if needed (e.g., react-native-bootsplash, react-native-safe-area-context)
   - Never skip steps without user confirmation

8. **Post-upgrade checklist:**
   - Provide a testing checklist including:
     - Clean builds for both platforms
     - New Architecture verification
     - Third-party integrations testing
     - Navigation and animations
     - Device-specific features (camera, location, notifications, etc.)

9. **Documentation:**
   - Summarize all changes made
   - List any manual follow-up actions required
   - Note any dependencies that need updates
   - Provide links to relevant release notes

## Best Practices to Follow

- Use the manual upgrade approach with diff analysis (not react-native upgrade CLI)
- Upgrade incrementally (one major version at a time) when jumping multiple versions
- Enable New Architecture in current version before upgrading if it's required in target
- Clear all caches after upgrade (metro, gradle, pods, derived data)
- Test thoroughly on both iOS and Android before considering upgrade complete

## Resources

- Upgrade Helper: https://react-native-community.github.io/upgrade-helper/
- RN Diff Purge: https://github.com/react-native-community/rn-diff-purge
- React Native Docs: https://reactnative.dev/docs/upgrading

---

Start by determining the current and target versions, then proceed with research and planning before making any changes.

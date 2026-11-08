## React project conventions

The `react-native` and `react-web` kits select this shared React guidance and the
`review-react` and `review-typescript` skills; `react-base` selects them alone.

For static analysis and tests use the project's own scripts directly (`yarn type-check`,
`yarn lint`, `yarn test`, or the npm/pnpm/bun equivalents the lockfile implies); for library
docs use `/research-tech`.

### Before writing components

- Check the `react` version in `package.json` before reaching for newer APIs
  (`useActionState`, `useOptimistic`, `use`, `useEffectEvent`).
- Check whether React Compiler is enabled (`babel-plugin-react-compiler`, configured in the
  Babel, Vite, Next.js or Expo config). When it is, don't add `useMemo`, `useCallback` or
  `memo` by hand; the compiler memoizes, and manual wrappers only add noise.
- Derive values during render instead of mirroring them into state, and keep effects for
  synchronizing with something outside React. Logic caused by a user action goes in the
  event handler.
- Use the project's existing data-fetching and state libraries rather than fetching in
  effects or adding a new store.

### Reviewing

`/review-react` covers judgment-level React review (state placement, effects, keys and
boundaries, render cost, platform pitfalls) and defers to `eslint-plugin-react-hooks` for the
mechanical rules; `/review-typescript` covers type design. `/code-review` includes both
automatically when they apply.

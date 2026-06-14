<!--
  This repository follows the AI-driven DDD/BDD/SDD/TDD process.
  See docs/ai-driven-development.md. Link the artifacts this PR produces or
  advances so reviewers can review the right thing for the right phase.
-->

## Summary

<!-- What does this PR change, and why? -->

## Related Issue

Closes #

## Pipeline phase

<!-- Which phase(s) does this PR cover? -->

- [ ] DDD (domain docs)
- [ ] BDD (feature files)
- [ ] SDD (contract / spec)
- [ ] TDD (implementation)

## Artifact links

<!-- Link the artifacts touched. Use "n/a" where a phase does not apply. -->

- Domain diff: <!-- docs/domain/*.md or n/a -->
- Feature file(s): <!-- features/*.feature or n/a -->
- Spec: <!-- docs/api/openapi.json, docs/specs/*.md, features/specs/*.spec.feature or n/a -->
- ADR: <!-- docs/adr/NNNN-*.md or n/a -->

## Verification

<!-- Exact commands run and their pass/fail status. -->

```
uv run pytest
```

## Reviewer notes

- Owners of changed domain/ADR files are requested automatically via CODEOWNERS.
- Confirm every new `.feature` / `.spec.feature` has executing step definitions.

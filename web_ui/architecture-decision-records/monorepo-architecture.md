# Monorepo architecture (14.05.2025)
___

## Context
We currently maintain two separate applications that share common components, notably intel admin and geti. However, the existing code structure lacks clear boundaries, leading to tight coupling and cyclic dependencies. This has made it difficult to scale the applications or reuse components effectively.

The current directory structure looks like this:
```
/src
    /core
    /pages
    /intel-admin-app
    /shared
    ...
```
This structure does not enforce clear ownership or dependency direction, making it challenging to manage changes, isolate functionality, or promote reuse across applications.

## Decision
We decide to adopt monorepo architecture to better organize our codebase and manage dependencies between applications and shared components.
- Each application will reside in its own top-level directory.
- Shared components will be extracted into clearly defined packages.

## Consequences
Pros:
- Components will be organized into well-defined packages, reducing coupling and making the codebase easier to understand and maintain.
- Shared components/logic can be extracted into standalone packages, making it easier to reuse across applications or even publish externally.

Cons:
- Setting up the monorepo requires upfront effort, including choosing the right tooling and restructuring the existing codebase.
- CI/CD pipelines might need to be reconfigured to handle the new code structure.

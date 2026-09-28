# Shared GitHub workflow

1. One teammate creates the repository and adds the others as collaborators.
2. Protect `main` when possible.
3. Nobody develops directly on `main`.
4. Create a branch:
   - `feature/frontend`
   - `feature/translation`
   - `feature/backend`
5. Commit small, descriptive changes.
6. Push the branch.
7. Open a Pull Request.
8. Another teammate reviews it.
9. Merge into `main` after review.

Example:

```bash
git clone <REPOSITORY_URL>
cd risalah-task2

git checkout -b feature/frontend
git add .
git commit -m "feat: create first atlas interface"
git push -u origin feature/frontend
```

GitHub branches are designed to isolate work, and Pull Requests are the normal workflow for proposing and reviewing changes before merging.

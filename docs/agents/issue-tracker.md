# Issue tracker

Issues and specs live in GitHub Issues for `nguyennhan18/lesson-plan-generator`, the repository configured as `origin`. Use the `gh` CLI. Before the first issue creation in a session, run `gh repo view --json nameWithOwner` to check the target. If `gh` resolves a different repository, pass `--repo nguyennhan18/lesson-plan-generator` explicitly.

## Issue operations

- **Publish a ticket or spec.** Create an issue with `gh issue create --title "..." --body-file <path>`. Use a Markdown file for multiline bodies.
- **Fetch a ticket.** Run `gh issue view <number> --json number,title,body,labels,comments`.
- **List tickets.** Run `gh issue list --state open --json number,title,body,labels`. Use `--label` and `--state` to limit the results. Fetch individual tickets for comments.
- **Comment.** Run `gh issue comment <number> --body-file <path>`.
- **Apply or remove a label.** Run `gh issue edit <number> --add-label "<label>"` or `gh issue edit <number> --remove-label "<label>"`. See `triage-labels.md` for the label mapping.
- **Close a ticket.** Post the reason with `gh issue comment`, then run `gh issue close <number>`. Post the comment separately so it is recorded when a ticket is already closed.

## Sub-issues and dependencies

- **Link a sub-issue.** Use `gh issue create --parent <parent> ...` or `gh issue edit <parent> --add-sub-issue <child>` if supported by the installed CLI. Otherwise use `gh api --method POST repos/nguyennhan18/lesson-plan-generator/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>`. If native sub-issues are unavailable, put `Part of #<parent>` at the top of the child issue.
- **Record a blocker.** Use GitHub's native dependencies with `gh issue create --blocked-by <n>,<n> ...` or `gh issue edit <child> --add-blocked-by <blocker>` if supported by the installed CLI. Otherwise use `gh api --method POST repos/nguyennhan18/lesson-plan-generator/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`. Retrieve numeric database IDs for either API call with `gh api repos/nguyennhan18/lesson-plan-generator/issues/<n> --jq .id`. If native dependencies are unavailable, put `Blocked by: #<n>, #<n>` at the top of the blocked issue.
- **Check blockers.** Run `gh api repos/nguyennhan18/lesson-plan-generator/issues/<n> --jq .issue_dependencies_summary.blocked_by` to count open native blockers. When using the textual `Blocked by:` fallback, check each listed issue's state. A ticket is unblocked when every blocker is closed.

## Pull requests as a triage surface

**PRs as a request surface: no.**

If this flag is set to `yes`, triage external PRs with the same label mapping as issues. Use `gh pr view <number>` for the body, `gh pr view <number> --comments` for comments, and `gh pr diff <number>` for the diff. Use `gh pr comment`, `gh pr edit`, and `gh pr close` for authorized updates. Use `gh api --paginate 'repos/nguyennhan18/lesson-plan-generator/pulls?state=open'` to list open PRs and filter out authors associated as `OWNER`, `MEMBER`, or `COLLABORATOR`. Issues and PRs share a number space. If the item type is unclear, try `gh pr view <number>` and then `gh issue view <number>`.

## Wayfinding

- **Map.** Keep Notes, Decisions-so-far, and Fog in one issue labeled `wayfinder:map`.
- **Child tickets.** Link each ticket to the map as a sub-issue and label it `wayfinder:<type>`, where `<type>` is `research`, `prototype`, `grilling`, or `task`. If native sub-issues are unavailable, add the child to a task list in the map and put `Part of #<map>` at the top of the child issue.
- **Next ticket.** Read the map's open children in map order and pick the first with no open blockers and no assignee.
- **Claim.** Assign the ticket to yourself with `gh issue edit <number> --add-assignee @me`.
- **Resolve.** Comment with the result, close the ticket, and add a link to the supporting context under Decisions-so-far on the map.

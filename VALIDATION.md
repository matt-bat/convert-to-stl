# Release validation — 1.0.0

The following current release summary supersedes the earlier UI-development counts below.

- 25 source tests: 18 converter checks and 7 native UI-flow checks, including adaptive settings.
- Eight frozen-executable fixtures cover seven box formats and a curved STEP sphere.
- Native packaged window rendering and single-file manual-start behavior are checked.
- Default and minimum-size layouts were visually inspected on this Windows x64 PC.
- Release source/portable ZIPs are checked for CRC integrity and have SHA-256 hashes.
- These checks use generated samples. No all-vendor compatibility, exhaustive security,
  full accessibility, all-Windows-version, or clean-machine certification is claimed.
- Source suite and packaging checks are rerun for the release before publication.

## Earlier UI validation record — 2026-10-03

### Development validation

Current UI revision checked on this Windows x64 PC, 2026-10-03.

## Current checks

- 24 automated tests pass: 18 conversion regressions and 6 native UI flow tests. The UI suite was rerun after the last styling changes and all 6 pass. Logs: `artifacts/tests.txt`, `artifacts/ui-tests.txt`.
- Conversion regressions cover supported mesh/CAD formats, 3MF assembly transforms and production resources, units, original-file preservation, duplicate names, Unicode paths, corrupt input, open-edge warnings and CAD sphere pole cleanup.
- UI tests verify a single added file does not auto-convert, a manually started batch excludes later additions, retry only requeues, Stop preserves pending work, a missing output folder prevents startup, and keyboard selection/removal/conversion works.
- Actual revised GUI converted STEP, 3MF and a curved STEP in a manual batch. Default and 860 x 520 logical-pixel minimum window sizes were captured and visually reviewed.
- The final UI release passed eight packaged-executable conversions with Python removed from PATH. Its native window rendered successfully, and launching it with a single 3MF file produced no STL without an explicit Convert action. Evidence: `artifacts/package-verification.json` and `artifacts/packaged-ui.png`.

## Spatial Canvas review

User/context: local Windows utility for selecting one or many 3D files, adjusting destination/units/detail, converting explicitly, and inspecting saved results. User confirmed the got-skills UI Spatial Canvas system.

Flow: add/drop files -> review the queue and settings -> Convert -> inspect selected result or open output. All work stays at the root. No separate screens or home button are necessary because the root workspace is always present. The standard file picker, details dialog and Explorer are reversible contextual actions.

| Principle | Assessment |
| --- | --- |
| Clarity/hierarchy | Pass: queue is primary; settings adjacent; one explicit Convert action. |
| Consistency/predictability | Pass: adding, folder selection and retry never initiate conversion. |
| System status | Pass: Ready, Converting, Saved, Check mesh, Error and Stopped are text-labelled. Batch progress counts completed files rather than inventing within-file percentages. |
| User language | Pass: files, save location, source units, surface detail. |
| Control/recovery | Pass: Stop, non-destructive Remove, Requeue failed, protected originals. |
| Error prevention | Pass: destination required; batch settings frozen; later additions deferred. |
| Recognition | Pass: visible add/convert controls and field explanations; dropdown indicators retained. |
| Efficiency | Pass: multi-select/drop, explicit batch execution, contextual selection actions. |
| Accessibility | Partial: native keyboard controls, focus order, focus borders, selectable result text and non-colour status verified; no full screen-reader certification. |
| Resizing | Pass at checked default and minimum viewports; settings and list scroll locally when necessary. Every Windows display-scaling combination was not tested. |
| Motion restraint | Pass: no decorative animations. |
| Content-first presentation | Pass: no oversized drop banner, promotional badges, nested cards or route changes. |

The small-window settings scrollbar and file-list scrollbar are intentional Spatial Canvas exceptions for content access. The overall window does not scroll; Convert and Stop stay in the footer. Existing source files and independent conversion workers are unchanged.

## Limits

Generated fixtures demonstrate representative compatibility, not every vendor extension or arbitrary malformed CAD file. Conversion is not a full mesh-repair guarantee. Large-file stress behavior, cancellation at every native-code point and other Windows releases were not exhaustively tested. Application conversion paths do not request network resources, but tests did not run behind a network-denial firewall.


Glass studio refinement: 25 tests passed, including mixed-format adaptive controls. Default and minimum-size native window screenshots inspected. Translucency is drawn inside the app and does not require Windows compositor effects.

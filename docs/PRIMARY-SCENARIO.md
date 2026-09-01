# Primary Scenario: Status Normalization Trigger/Backfill Race

## Purpose

This scenario demonstrates a migration bug that exists only because several individually reasonable actions occur in a harmful order. It is synthetic, financially understandable, and executable without external systems.

## Business context

An ecommerce application stores order status as text in `orders.status`. The team is normalizing status values into an `order_statuses` lookup table and introducing `orders.status_id`.

During the rollout:

- The legacy application reads and writes `orders.status`.
- A legacy payment-event trigger updates only `orders.status` to `paid`.
- A backfill populates `orders.status_id` from the current text value.
- The new application reads `orders.status_id`.
- A compatibility trigger or dual-write behavior is intended to keep both representations aligned, but the unsafe rollout activates it too late.

## Simplified data model

- `order_statuses(id, name)` contains `pending`, `paid`, `shipped`, and `refunded`.
- `orders(id, status, status_id, ...)` contains legacy and new representations during migration.
- `payment_events(id, order_id, event_type, ...)` receives a confirmed-payment event.
- A trigger responds to a payment confirmation by updating the associated order.

All data is synthetic.

## Business invariant

At every configured compatibility boundary, every non-null `status_id` must resolve to the same semantic status as `orders.status`.

Verifier convention:

> The invariant query returns the rows where the text status and lookup status disagree. Zero rows means pass; one or more rows means fail.

The actual implementation must store the assertion as checked-in SQL and preserve returned evidence rows.

## Unsafe rollout phases

1. **Seed:** order 42 is `pending`; `status_id` is absent/null.
2. **Expand:** create/populate the lookup table and add nullable `status_id`.
3. **Backfill:** convert existing `pending` to its lookup identifier.
4. **Compatibility gap:** legacy payment trigger still updates only text status.
5. **New application deployment:** new reader begins using `status_id`.
6. **Late compatibility update:** dual-write or trigger correction is activated after the dangerous window.
7. **Contract:** legacy representation would eventually be removed.

## Verified failing schedule

The evaluator may know this schedule; the specialised agent prompt must not be handed the answer.

1. Seed order 42 as text `pending`.
2. Expand the schema.
3. Backfill order 42, setting its identifier to `pending`.
4. Insert a confirmed payment event through the legacy path.
5. The legacy trigger updates text status to `paid` but leaves `status_id` as `pending`.
6. Run the compatibility invariant: it fails on order 42.
7. The new reader observes `pending` despite the confirmed payment.

## Consequence

The order has been paid, but the new application can treat it as unpaid. A refund request, fulfilment decision, or customer-support workflow can therefore make the wrong decision.

The submission must avoid claiming actual financial loss; it demonstrates a synthetic failure with a plausible financial consequence.

## Why static checks are insufficient

- The schema is valid.
- The backfill mapping is individually correct when it executes.
- The legacy payment trigger is individually correct for the legacy representation.
- The new reader is individually correct for the new representation.
- The failure appears only after the row is backfilled and then changed by legacy behavior before compatibility coverage is active.

## Permitted repair

The primary bounded repair is:

1. Activate compatibility behavior before the first backfill batch.
2. Make the payment trigger update both representations while both exist.
3. Run a catch-up reconciliation after compatibility activation.
4. Check the invariant before enabling new-only reads.

Alternative permitted repair: delay new-only reads and use a checked-in compatibility read path until reconciliation completes.

The agent may select and explain a permitted repair. It may not generate arbitrary production SQL.

## Human-approved replay

After explicit approval, the executor creates a fresh sandbox using the repaired scenario variant and replays the identical named schedule. The report must show:

- Original trace and failed evidence row.
- Repair selected and approval event.
- Repaired trace.
- Invariant result at the same boundary.

## Additional benchmark variants

### U2: Legacy update after a row's backfill batch

A legacy cancellation updates only the text status after that row has already been processed by the backfill. The new representation remains stale.

### U3: Cutover before backfill completion

New-only reads begin while an eligible order remains unbackfilled, causing a null or incorrect semantic status.

### S1: Compatibility-first safe rollout

The trigger updates both representations before backfill starts, followed by reconciliation and invariant verification before cutover.

### S2: Compatibility-read safe rollout

The new application uses a declared compatibility read path during the transition, and contract occurs only after backfill completion and verification.

These variants should reuse the same schema and operation vocabulary. Do not construct separate subsystems for each.

## Visual timeline requirements

The primary report should contain swim lanes for:

- Migration coordinator.
- Backfill worker.
- Legacy application/trigger.
- New application reader.
- SQL verifier.

Highlight the first mismatch in red and display the offending row values. The repaired replay should align the same schedule beside it in green.


# Transaction Mechanics

Applies to all HX products (insurance policies, parking bookings, hotel stays, etc.)

## Core Date Concepts

| Date | Definition |
|------|-----------|
| **Book Date** | When the customer made the booking/purchased the policy |
| **Stay Date** (or travel date) | When the customer uses the product |

The gap between these = **lead time** or **booking lag**.

## Revenue Recognition

Revenue is recognised on a **stay basis** (when the trip happens), not a booking basis. Until the stay occurs, the transaction can still cancel.

## Booked GP vs Stay-Date GP

| Basis | Definition | When Used |
|-------|-----------|-----------|
| **Booked GP** (default) | GP attributed to the book date | Default in all standard reports. If unqualified, GP = booked GP. |
| **Stay-Date GP** | GP attributed to the stay date | Only when the report explicitly references "stays". |

## Cancellations

- Typical daily cancellation rate: ~10% of bookings (UK Distribution benchmark)
- **Net bookings** = new bookings minus cancellations in a given period
- Not all cancellations are genuine — some are amendments (cancel + rebook), estimated at ~4% of the 10%

# Tapri Peak-Hour Loss Tracker

A small, dependency-free Python command-line tool for summarising item handovers and payment discrepancies at the NIT Silchar tapri. The intended beneficiary is Rupam Daa, the owner.

> ## Important data disclosure
> The current `data.csv` contains **24 simulated demonstration rows**, not field observations. Every row is marked `SIMULATED_NOT_FIELD_DATA`. The dates, times, transaction events, crowd levels, and payment outcomes are illustrative and were not collected at the stall. The ₹130 output is a software demonstration, **not a claim about Rupam Daa or the actual business**. Do not submit these rows as personally collected field data.

## What it does

- Reads a CSV of item handovers.
- Calculates the listed-price value of quantities explicitly marked `observed_unpaid`.
- Groups potential value by time window and item.
- Excludes `needs_follow_up` rows from the estimate.
- Validates timestamps, prices, quantities, crowd levels, status values, and data provenance.
- Displays a prominent simulated-data warning when the file is synthetic.
- Rejects a CSV that mixes simulated and field-observed rows.

The tool does not identify customers, establish intent, prove theft, or estimate a weekly/monthly loss.

## Menu and prices

The following prices were supplied for this project and should be confirmed with Rupam Daa before they are treated as current.

| Item | Price |
|---|---:|
| Marlboro Advance | ₹15 |
| Gold Flake | ₹15 |
| Flake | ₹10 |
| Tropical | ₹10 |
| Tea | ₹10 |
| Boiled Maggi | ₹20 |
| Fried Maggi | ₹30 |
| Poach | ₹20 |
| Omelette | ₹20 |
| Bread Omelette | ₹30 |
| Cake | ₹10 |
| Biscuits | ₹5 |

## Run locally

Requires Python 3.10+; no third-party packages are required.

```bash
python app.py
```

This reads `data.csv` and prints a report. The bundled file is simulated, so the report prominently labels itself as a demo.

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Demonstration output

The current synthetic dataset has 24 illustrative rows:
- 14 rows marked paid
- 8 rows marked as illustrative unpaid handovers
- 2 rows marked uncertain and excluded from the calculation
- 8 unpaid units, with an illustrative potential value of **₹130**

The value is calculated as:

`(qty_handed_over - qty_paid_for) × unit_price`

Only rows with `verification_status=observed_unpaid` contribute. Uncertain entries do not.

## CSV format

| Column | Meaning |
|---|---|
| `timestamp` | Local timestamp in `YYYY-MM-DD HH:MM` |
| `item` | Product name |
| `unit_price` | Price per unit in INR |
| `qty_handed_over` | Units handed over |
| `qty_paid_for` | Units for which payment was seen |
| `crowd_level` | `low`, `medium`, or `high` |
| `observation_note` | Neutral note describing what was observed |
| `verification_status` | `paid`, `observed_unpaid`, or `needs_follow_up` |
| `data_origin` | `SIMULATED_NOT_FIELD_DATA` or `FIELD_OBSERVATION` |

For real fieldwork, replace the demonstration file with genuinely recorded entries and set every real row's origin to `FIELD_OBSERVATION`. Do not mix synthetic and real rows in one file. If payment is uncertain, record `needs_follow_up`; do not infer intent.

## Fieldwork protocol

The assignment requires an actual visit, at least 20 real entries, a conversation with the named person, two timestamped photos, and a personal reflection. These cannot be reconstructed from synthetic data.

1. Ask Rupam Daa for permission and confirm the problem in his own words.
2. Observe for at least 20 minutes without disrupting the stall.
3. Log at least 20 real handover events, including time, item, price, quantity handed over, quantity paid for, and crowd level.
4. Mark `observed_unpaid` only if you directly observed the handover and that payment was not made before the customer left. Use `needs_follow_up` if unclear.
5. Do not collect customer names, faces, phone numbers, or other identifying details.
6. Ask permission before photographing the stall or owner; avoid identifiable customers.

See `fieldwork.md` for the interview and observation template. The reflection in `reflection.md` must be written by the student without AI. Add actual AI conversation exports to `ai-chats/`.

## What it gets wrong / limitations

- A payment may be made later, by another person, or through UPI outside the observer's view.
- An apparent discrepancy does not prove deliberate non-payment or theft.
- Incorrect prices or quantities produce incorrect estimates.
- Crowd level is subjective unless a consistent rule is defined and used.
- A short observation window is not representative of a whole day or month.
- A discrepancy may come from shared orders, delayed payment, a discount, or an observation/recording mistake.
- The tool does not integrate with a POS, inventory system, CCTV, or payment provider.

## Research sources

1. Clarke, R. V. & Petrossian, G. (2012), [Shoplifting, 2nd Edition](https://www.popcenter.org/content/shoplifting-2nd-ed), Center for Problem-Oriented Policing. Used as background for framing questions about small goods and prevention; it is not evidence about this tapri.
2. UK Home Office (2014), [Crime against businesses: Detailed findings from the 2013 Commercial Victimisation Survey](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/342577/crime-against-businesses-detailed-13.pdf). Used for terminology and background; UK results are not transferable estimates for NIT Silchar.

## AI usage

AI assisted with research framing, implementation, validation logic, tests, and documentation. It did not conduct the field visit, interview the owner, collect real observations, take photos, or write the student's reflection. Export the actual AI conversations used during development into `ai-chats/` before submission.

## Submission checklist

- [ ] Complete the real visit and owner conversation.
- [ ] Record at least 20 genuine observations in `data.csv`.
- [ ] Add two original timestamped photos with permission.
- [ ] Complete `fieldwork.md` with the real details and what surprised you.
- [ ] Write `reflection.md` yourself, without AI.
- [ ] Add actual AI chat exports to `ai-chats/`.
- [ ] Record and link the requested 3-minute demo using the real dataset.
- [ ] Replace the simulated demo output in this README with the real output, clearly describing its limitations.

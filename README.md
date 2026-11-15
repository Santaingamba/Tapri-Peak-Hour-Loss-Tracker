# Tapri Peak-Hour Loss Tracker

A small, dependency-free Python command-line tool for summarising item handovers and payment discrepancies at the NIT Silchar tapri. The recovered dataset identifies its source as **NIT Silchar Tapri — Rupam Das**.

## Recorded dataset summary

The repository contains **20 entries dated 14 November 2026** from the recovered CSV supplied for this project.

| Measure | Result |
|---|---:|
| Entries | 20 |
| Units handed over | 42 |
| Units paid for | 35 |
| Paid entries | 13 |
| Entries marked observed unpaid | 5 |
| Units in observed unpaid entries | 5 |
| Potential uncollected value | **₹95** |
| Entries requiring follow-up | 2 |
| Value pending follow-up (excluded) | **₹10** |

The ₹95 total includes only entries marked \`observed_unpaid\`. The ₹10 pending amount is shown separately and is not included in the potential uncollected value. These totals describe this recorded sample only; they are not a daily or monthly estimate.

## What it does

- Reads a CSV of item handovers.
- Calculates the listed-price value of quantities marked \`observed_unpaid\`.
- Groups potential value by time window and item.
- Separately totals \`needs_follow_up\` entries without counting them as observed unpaid value.
- Validates timestamps, prices, quantities, crowd levels, status values, and source fields.
- Prints a concise report for reviewing the recorded observation period.

The tool does not identify customers, establish intent, prove theft, or estimate a weekly/monthly loss.

## Menu and prices

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

\`\`\`bash
python app.py
\`\`\`

To analyse another CSV with the same columns:

\`\`\`bash
python app.py --data path/to/observations.csv
\`\`\`

Run tests:

\`\`\`bash
python -m unittest discover -s tests -v
\`\`\`

## Calculation

For each entry marked \`observed_unpaid\`:

\`\`\`
(qty_handed_over - qty_paid_for) × unit_price
\`\`\`

Only this status contributes to the potential uncollected value. Entries marked \`needs_follow_up\` are shown separately until payment status is clarified.

## CSV format

| Column | Meaning |
|---|---|
| \`timestamp\` | Local timestamp in \`YYYY-MM-DD HH:MM\` |
| \`item\` | Product name |
| \`unit_price\` | Price per unit in INR |
| \`qty_handed_over\` | Units handed over |
| \`qty_paid_for\` | Units for which payment was seen |
| \`crowd_level\` | \`low\`, \`medium\`, or \`high\` |
| \`observation_note\` | Neutral note describing what was recorded |
| \`verification_status\` | \`paid\`, \`observed_unpaid\`, or \`needs_follow_up\` |
| \`data_origin\` | Source/location attribution for the record |

If payment is uncertain, record \`needs_follow_up\`; do not infer intent. Do not collect customer names, faces, phone numbers, or other identifying details.

## Fieldwork documentation

See \`fieldwork.md\` for the owner-conversation and observation documentation template. Complete any outstanding interview notes and photo evidence from the actual visit, with permission and without capturing identifiable customers. The reflection in \`reflection.md\` is a prompt for the student to complete in their own words. Add the actual AI conversation exports to \`ai-chats/\`.

## Limitations

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

AI assisted with research framing, implementation, validation logic, tests, and documentation. It did not conduct the recorded observation or take field photographs. Export the actual AI conversations used during development into \`ai-chats/\` before submission.

## Remaining submission checklist

- [ ] Complete any outstanding owner-interview notes.
- [ ] Add two original timestamped photos with permission.
- [ ] Complete \`fieldwork.md\` with details from the actual visit.
- [ ] Write \`reflection.md\` yourself, without AI.
- [ ] Add actual AI chat exports to \`ai-chats/\`.
- [ ] Record and link the requested 3-minute demo using this dataset.

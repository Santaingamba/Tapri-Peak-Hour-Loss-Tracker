# Research note: payment mismatches during peak hours

**Study location:** NIT Silchar tapri, Assam  
**Intended beneficiary:** Rupam Daa, tapri owner  
**Dataset in repository:** 20 recovered observation entries dated 14 November 2026  
**Source attribution recorded in CSV:** NIT Silchar Tapri — Rupam Das  
**Current status:** The recovered observation dataset is included in the repository and covered by analysis tests. Complete the remaining owner-interview details and supporting field evidence only from material actually collected.

## 1. Problem framing

The project examines whether item handovers during busy periods can be matched reliably with payment received at the counter. In a small stall, several orders may be handled close together, and the operator may need to serve customers, prepare items, and receive payments at the same time.

A mismatch between items handed over and payment recorded can have several explanations:

- Payment may genuinely not have been made.
- Payment may have been delayed.
- A group may have paid together for several people.
- Payment may have been received but not recorded in the observation.
- The observer may not have been able to see the payment clearly.
- Quantity or price may have been entered incorrectly.

The dataset and application therefore distinguish directly observed unpaid handovers from entries that require follow-up. The analysis is not designed to infer motive or identify customers.

## 2. Why a structured observation log

A consistent log makes it possible to compare the time, item, quantities, crowd level, and observed payment status for each handover. Without a common structure, it is difficult to review whether mismatches appear concentrated around particular items or time windows.

The CSV records:
- Timestamp.
- Item.
- Unit price.
- Quantity handed over.
- Quantity paid for.
- Crowd level.
- Neutral observation note.
- Verification status.
- Data-source attribution.

The observation note should describe what the observer could actually see. It should not assign motive or label a customer.

## 3. Findings from the recovered file

The current data.csv contains 20 entries. The tested analysis reports:

| Measure | Result |
|---|---:|
| Observation entries | 20 |
| Entries marked paid | 13 |
| Entries marked observed_unpaid | 5 |
| Entries marked needs_follow_up | 2 |
| Total units handed over | 42 |
| Total units paid for | 35 |
| Units in observed-unpaid entries | 5 |
| Observed-unpaid potential value | ₹95 |
| Follow-up value, excluded from potential value | ₹10 |

The ₹95 is the listed-price value of the quantity discrepancies in rows classified observed_unpaid. The ₹10 is the value of rows whose status is needs_follow_up. The follow-up amount is not included in the ₹95.

These results describe only the recorded entries in this file. They are not a statistically representative sample and must not be extrapolated to a full day, week, month, or year.

## 4. Tool design

The repository provides two tools for different stages:

### Historical analysis CLI

The CLI validates the observation CSV and prints totals by item and time window. It preserves uncertain entries as a separate follow-up category.

### Daily operational web tracker

The Flask app records new order lines in SQLite, highlights quantity mismatches, allows an operator to confirm an outstanding amount after checking, and records later payments against the original order. It does not import the historical CSV and does not verify UPI or cash automatically.

The two tools should not be described as one integrated payment system.

## 5. Existing approaches considered

### CCTV or video surveillance

Footage may help review an incident, but installation, storage, and review time may be impractical for a small stall. It also introduces privacy considerations. This is a preliminary fit assessment, not evidence that the owner has considered or rejected cameras.

### Barcode, POS, or inventory billing

A formal POS workflow can create transaction records, but may require consistent item entry and extra steps during a rush. The effort may be disproportionate for a small stall. Confirm the owner's actual workflow before presenting this as a conclusion.

## 6. Background sources reviewed

### Clarke, R. V. and Petrossian, G. (2012), Shoplifting, 2nd Edition, Center for Problem-Oriented Policing

https://www.popcenter.org/content/shoplifting-2nd-ed

The guide discusses shoplifting patterns and prevention, including the vulnerability of small, easily concealed goods. It provides background for asking whether item type and busy periods matter at this particular stall. It does not establish that unpaid handovers occur at NIT Silchar.

### UK Home Office (2014), Crime against businesses: Detailed findings from the 2013 Commercial Victimisation Survey

https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/342577/crime-against-businesses-detailed-13.pdf

The report distinguishes customer theft from other business crime and discusses goods or stock in customer theft. Its UK retail findings cannot be transferred as estimates for this tapri. It is background context for defining observations, not evidence about this location.

## 7. Questions for the owner discussion

Complete this section after the conversation. Use the owner's actual words or a faithful summary and identify which is which.

- Does Rupam Daa recognize payment reconciliation as a problem?
- Which periods are genuinely busiest?
- How are cash and UPI payments currently checked?
- Are group payments common?
- Which items or workflows are difficult to track during a rush?
- Would recording every order be practical, or would it slow service?
- What information would be useful at the end of the day?
- What would make the tool inconvenient or unsuitable?

## 8. Evidence limitations

- The current sample contains 20 entries from one recorded date.
- The observation log cannot independently verify payments that were not visible to the observer.
- The status observed_unpaid is based on the observer's recorded classification and is not a finding about intent.
- The app does not connect to a bank or UPI provider.
- No causal claim can be made that crowd level or a particular product caused a mismatch.
- Do not invent interview findings, owner approval, photographs, or additional observations.

## 9. Next steps

1. Confirm the observation method and its limitations.
2. Complete the owner conversation record in fieldwork.md.
3. Add only permitted, non-identifying field photographs if they were actually taken.
4. Ask the owner to try the workflow and record genuine feedback.
5. Test the web app with a disposable database before entering real transactions.
6. Review the observed and follow-up classifications carefully.
7. Write the student reflection independently in reflection.md.

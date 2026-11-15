# Daily user guide

This guide describes the current features of the web tracker.

## Sign in

Open the local application address and enter the owner password configured through TAPRI_ADMIN_PIN. The app keeps the signed-in session for up to eight hours. Use the Lock button when finished, especially on a shared device.

The application is designed as a single-owner tool. It does not currently provide separate accounts or permission levels for multiple staff members.

## Record an order

On the dashboard, complete the order form:

| Field | What to enter |
|---|---|
| Item | Product handed over, such as Tea or Fried Maggi |
| Unit price | Actual price charged for one unit, in rupees |
| Quantity served | Number of units handed over |
| Quantity paid for | Number of units covered by payment already received |
| Payment method | Cash, UPI, mixed, or unknown |
| Crowd level | Low, medium, or high |
| Note | Optional short operational note; do not enter customer identity |

The item field offers suggestions from products.csv. Suggestions do not lock the price. Enter the actual current unit price and check it before saving.

Quantity served must be a positive whole number. Quantity paid for can be zero, but cannot exceed quantity served. The app accepts prices with up to two decimal places.

After saving, the dashboard lists the order. If the quantities differ, the app opens the order detail page so the operator can review the outstanding amount.

## Understand the statuses

- **Settled:** The calculated outstanding balance is zero.
- **Check payment:** The initial quantities differ and the remaining amount has not been marked confirmed unpaid.
- **Confirmed unpaid:** An operator has explicitly confirmed that the amount remains unpaid after checking. This is still an operator-entered status, not proof of a customer's intent.

The dashboard's Needs checking figure is the total current outstanding amount across today's orders, including entries not yet confirmed. It should not be described as a proven loss.

## Reconcile a mismatch

Before confirming an amount as unpaid:

1. Check whether cash was collected but not entered.
2. Check the relevant UPI transaction record.
3. Consider whether a group paid together or payment was delayed.
4. Check whether the served and paid quantities were entered correctly.
5. If the amount is still outstanding after these checks, use Confirm still unpaid on the order detail page.

The confirmation can be toggled off if later review shows the classification was wrong.

## Record a later payment

Open the original order and use Record later payment.

- Enter the amount actually received, in rupees.
- Select cash, UPI, or other.
- Add an optional note without personal customer information.
- Save the recovery.

The app prevents a recovery larger than the current outstanding balance. It stores each recovery separately with its own timestamp and method. The remaining balance is reduced by the recorded recovery amount.

A recovery is recorded as an amount, not a number of units. This supports partial payments but means the operator must ensure the amount corresponds to the original mismatch.

## Review daily activity and history

The dashboard displays today's order count, units served, payments recorded, and outstanding amount. The order list shows time, item, served quantity, initially paid quantity, balance, and status.

Select History to choose a date. The current history page displays up to 500 orders for the selected date. Open an order to inspect its recovery history and reconciliation state.

## Worked example

Suppose two cups of tea are served at ₹10 each and payment is received for one cup.

- Order value: ₹20
- Initially recorded payment: ₹10
- Initial mismatch: ₹10
- If ₹10 is received later, record a ₹10 recovery.
- Outstanding balance becomes ₹0 and the order displays Settled.

This example illustrates the arithmetic only. The app does not determine whether the initial mismatch was intentional.

## End-of-day routine

1. Open the dashboard and review every order marked Check payment or Confirmed unpaid.
2. Compare entries with cash and UPI records.
3. Record later payments against the original orders.
4. Correct any operational misunderstandings by toggling the confirmed status where appropriate.
5. Review the day's total outstanding amount.
6. Back up the SQLite database securely according to the owner's backup process.
7. Lock the app on shared devices.

## Current limitations

The current version does not support editing or deleting an order, splitting one order across multiple item rows, automatic UPI verification, inventory deduction, customer records, staff roles, CSV export, or cloud synchronization. If an order was entered incorrectly, do not silently alter the database; record the correction in an approved operational process and retain an audit trail outside the app until a correction workflow is implemented.

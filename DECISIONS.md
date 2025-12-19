# offRez Decisions (MVP)

Document of important product/technical decisions for the MVP.

## Persistency
- **DB choice:** SQLite3 (DEV and MVP production). Rationale: simple, zero-admin, works for MVP and tests; migration plan to PostgreSQL for scale later.

## Payments
- **Admin fee:** Manual Ecocash process (MVP). Instructions stored in app and communicated to users: Ecocash number `078196541` (Account holder: Brian Chinyanga).
- **Payment confirmation:** User pastes the Ecocash confirmation message into `/api/payments/confirm/`. Admin manually reviews and approves/rejects.
- **Unlock behavior:** After admin approval, user receives a limited allowance (default **3** landlord contact reveals for that university).

## Notes / Next steps
- Add guidance in the UI explaining the manual Ecocash flow and expected confirmation contents.
- Implement optional future migration plan to PostgreSQL and integration with payment providers (for online payments).

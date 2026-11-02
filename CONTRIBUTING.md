# Contributing

Issues are welcome. Outside pull requests are not accepted yet: the terms for them are still to be defined.

- **Bugs**: include the input, the observed output, the expected output and its source
  (a primary reference is better than another implementation).
- **Changes**: every behavioral change needs a test, and a requirement ID in
  `verification/REQUIREMENTS.md` if it changes what the library promises.
- **Data updates** (for example a new IERS Bulletin C): cite the bulletin number and update the
  expiry date together with the table; the MJD cross-check in the tests must still pass.
- Run `python -m pytest` before opening a pull request.

Code is published under the Apache License 2.0. No contribution terms apply yet, because no outside contribution is accepted.

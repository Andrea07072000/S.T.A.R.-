# Contributing

Issues and pull requests are welcome.

- **Bugs**: include the input, the observed output, the expected output and its source
  (a primary reference is better than another implementation).
- **Changes**: every behavioral change needs a test, and a requirement ID in
  `verification/REQUIREMENTS.md` if it changes what the library promises.
- **Data updates** (for example a new IERS Bulletin C): cite the bulletin number and update the
  expiry date together with the table; the MJD cross-check in the tests must still pass.
- Run `python -m pytest` before opening a pull request.

By submitting a contribution you agree that it is licensed under the Apache License 2.0, the
license of this repository, and that you have the right to submit it.

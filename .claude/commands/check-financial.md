Verify all financial calculations are correct. This is critical for legal compliance.

Steps:
1. Run all financial tests: `MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/test_interest.py tests/test_wik.py tests/test_payment_distribution.py -v`
2. Verify interest calculation with manual example:
   - EUR 5.000 principal, commercial interest (8%), 6 months → expected ~EUR 200
3. Verify WIK calculation with known values:
   - EUR 2.500 → EUR 375 (15%)
   - EUR 5.000 → EUR 625 (15% of 2500 + 10% of 2500)
   - EUR 10.000 → EUR 875
4. Verify art. 6:44 payment distribution:
   - Payment of EUR 500 on claim with EUR 100 costs + EUR 50 interest + EUR 1000 principal
   - Expected: EUR 100 to costs, EUR 50 to interest, EUR 350 to principal
5. Check for any `float` usage in financial code paths
6. Report: all calculations correct/incorrect with details

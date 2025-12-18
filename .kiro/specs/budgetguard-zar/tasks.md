# Implementation Plan

- [x] 1. Project Initialisation and Standards



  - [x] 1.1 Create .cursorrules with Senior Financial Architect persona and technical commandments

    - Define Decimal math requirements, ZAR formatting, Banker's Rounding standards
    - Include Google-style docstring requirements
    - _Requirements: All_
  - [x] 1.2 Create src/__init__.py with package version


    - _Requirements: 6.4_

- [x] 2. Core Data Models

  - [x] 2.1 Implement src/schema.py with RiskLevel enum and dataclasses
    - Create RiskLevel enum (HEALTHY, WARNING, CRITICAL, OVER_BUDGET)
    - Create Campaign dataclass with Decimal fields
    - Create CampaignAnalysis dataclass
    - Create AnalysisSnapshot dataclass
    - _Requirements: 1.5, 3.1, 4.1, 4.2, 4.3_
  - [x] 2.2 Write property test for Decimal type preservation
    - **Property 6: Decimal Arithmetic Preservation**
    - **Validates: Requirements 1.5, 4.5**

- [x] 3. Date Logic Module




  - [x] 3.1 Implement src/date_logic.py with DateManager class

    - Implement is_leap_year method
    - Implement get_days_in_month method with leap year handling
    - Implement get_days_remaining method (inclusive of current day)
    - Implement get_time_percentage method
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x] 3.2 Write property test for days remaining calculation


    - **Property 3: Days Remaining Calculation Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

- [x] 4. Pacing Engine Module





  - [x] 4.1 Implement src/calculator.py with PacingEngine class
    - Implement calculate_rds with Decimal arithmetic and ROUND_HALF_EVEN
    - Implement calculate_spend_percentage
    - Implement determine_risk_level with threshold logic
    - Implement analyse_campaign combining all calculations
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.5_
  - [x] 4.2 Write property test for RDS formula correctness
    - **Property 4: RDS Formula Correctness**
    - **Validates: Requirements 3.1, 3.4**
  - [x] 4.3 Write property test for risk classification


    - **Property 5: Risk Classification Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 5. Checkpoint - Verify Core Engine
  - Ensure all tests pass, ask the user if questions arise.

- [-] 6. Data Validation Module
  - [x] 6.1 Implement src/validator.py with DataValidator class

    - Implement CSV column validation
    - Implement parse_decimal with error handling
    - Implement validate_csv returning ValidationResult
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 6.2 Write property test for CSV parsing
    - **Property 1: CSV Parsing Preserves All Valid Rows**

    - **Validates: Requirements 1.1, 1.5**
  - [x] 6.3 Write property test for invalid value rejection

    - **Property 2: Invalid Monetary Values Are Rejected**
    - **Validates: Requirements 1.2, 1.3**

- [-] 7. Audit and Serialisation Module


  - [x] 7.1 Implement src/audit.py with AuditLogger class


    - Implement serialise_snapshot with Decimal to string conversion
    - Implement deserialise_snapshot with string to Decimal conversion
    - Implement save_to_file and load_from_file
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 7.2 Write property test for serialisation round-trip
    - **Property 7: Serialisation Round-Trip**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [-] 8. Excel Report Generation Module


  - [x] 8.1 Implement src/excel_generator.py with ExcelReporter class


    - Implement generate_report method
    - Implement _create_summary_sheet with aggregate metrics
    - Implement _create_detail_sheet with per-campaign data
    - Implement _apply_risk_formatting with conditional styling
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 8.2 Write unit tests for Excel report structure

    - Verify Finance Summary and Campaign Deep-Dive sheets exist
    - Verify required columns and formatting
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 9. Final Checkpoint - Complete Test Suite
  - Ensure all tests pass, ask the user if questions arise.

# PRD: Test Input Brief Feature

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-05-19 |
| **Status** | Draft |
| **Type** | Feature |
| **Author** | AI Requirement Agent |

---

## 1. Problem Statement
Users face delays in configuring experiments due to manual KPI validation and lack of sample size preview.

## 2. Business Value
Reducing setup time improves PM productivity and increases experiment throughput, leading to faster insights and potential revenue uplift.

## 3. Stakeholders
| Name | Role | Email |
|------|------|-------|
| Hemanth Kakaraparthi | Product Owner | hemanthkakaraparthi@gmail.com |
| TestOps Dev Team | Engineering | — |

## 4. Goals & Success Metrics
| Goal | Metric | Baseline | Target |
|------|--------|----------|--------|
| Reduce experiment setup time | minutes/experiment | ~45 min currently | < 15 min within 4 weeks of launch |

## 5. Scope
### In Scope (v1)
- Core feature flow
- API integration

### Out of Scope
- Mobile app
- Offline mode

## 6. Users & Personas
| Persona | Description | Key Need |
|---------|-------------|----------|
| Product Manager | Zone PM running A/B tests. | Fast experiment creation. |

## 7. Functional Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | User can create a new experiment from the dashboard. | Must Have |
| FR-02 | System validates KPI selection against data source. | Must Have |
| FR-03 | User can preview estimated sample size. | Should Have |

## 8. Non-Functional Requirements
| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-01 | Performance | Page initial render | < 2s on broadband |
| NFR-02 | Security | All endpoints behind SSO | 100% coverage |

## 9. User Stories

### US-01: Create a new experiment
**As a** Product Manager,
**I want to** start a new experiment from the My Experiments dashboard,
**So that** I can run an A/B test without involving the Data Science team.

| Priority | Story Points | Labels |
|----------|-------------|--------|
| Must Have | 5 | `frontend`, `react` |

**Acceptance Criteria:**
  - [ ] Create button opens 5-step wizard
  - [ ] All mandatory fields validated before save
  - [ ] Experiment appears in My Experiments list

---
### US-02: Validate KPI selection
**As a** Product Manager,
**I want to** ensure KPI is valid and has data before proceeding,
**So that** I avoid wasted experiments with incorrect KPIs.

| Priority | Story Points | Labels |
|----------|-------------|--------|
| Must Have | 3 | `backend`, `validation` |

**Acceptance Criteria:**
  - [ ] System checks KPI against Snowflake data
  - [ ] Invalid KPI triggers error message
  - [ ] User can re-select KPI without restarting wizard

---
### US-03: Preview sample size
**As a** Product Manager,
**I want to** see estimated sample size before launching experiment,
**So that** I can adjust parameters to meet statistical significance.

| Priority | Story Points | Labels |
|----------|-------------|--------|
| Should Have | 2 | `frontend`, `analytics` |

**Acceptance Criteria:**
  - [ ] Sample size displayed after KPI validation
  - [ ] Estimate updates when parameters change
  - [ ] Fallback estimate shown if query times out

---

## 10. Edge Cases & Error Scenarios
| Scenario | Expected Behaviour |
|----------|--------------------|
| User leaves wizard halfway through | Progress saved as draft; resumable. |
| KPI source returns no data | Show error and allow KPI re-selection. |

## 11. Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Snowflake query latency spikes | High — sample size estimator hangs | Add query timeout + fallback cached estimate. |

## 12. Technical Constraints
- FastAPI
- React
- ACS email relay
- Postgres
- AKS

## 13. Dependencies
- Snowflake connector in Data Onboarding

## 14. Assumptions
- Users authenticated via Azure SSO

## 15. Open Questions
- [ ] Should experiment drafts auto-expire after 30 days?

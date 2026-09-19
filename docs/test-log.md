# CourseFlow Test Log

This log records manual tests performed during development. Results should be updated honestly when behavior changes.

## Test 1 — Built-in sample syllabus

**Tester:** Project participant  
**Input:** Built-in six-deadline sample

Results:

- Six deadlines were extracted.
- Workload warnings appeared.
- Rejecting an event changed its approval state successfully.
- Reapproving the event worked successfully.
- Calendar download did not start inside the embedded development preview. The backend ICS test passes, so download must be retested in a normal deployed browser.

Learning:

- The approval workflow is understandable and responsive.
- Embedded previews may restrict generated file downloads.
- The date editing control was not immediately easy to understand and needs a usability improvement.

## Test 2 — Custom WEB 201 schedule

**Input:** Five dated lines plus one line without a date

Expected:

- Five deadlines
- Correct titles and dates
- Same-day warning for September 24
- “Read Chapter 5 before next class” ignored

Observed:

- Five deadlines were found.
- All extracted titles were correct.
- All extracted dates were correct.
- Workload warnings appeared.
- The undated Chapter 5 instruction was ignored.

Result: **Passed**

## Test 3 — PDF syllabus extraction

**Input:** `samples/sample-syllabus.pdf`

Expected:

- PDF accepted
- Five deadlines extracted
- Correct titles and dates
- Same-day warning for September 23
- Undated reading instruction ignored

Observed:

- The PDF was accepted successfully.
- Five deadlines were extracted.
- All titles were correct.
- All dates were correct.
- The September 23 conflict was shown.
- The undated reading instruction was ignored.

Result: **Passed**

## Test 4 — Popup editing and manual deadline entry

The participant selected a popup editor after finding the original inline date control difficult to use.

Observed:

- The Edit popup opened successfully.
- A deadline date was changed successfully.
- Workload warnings recalculated after the date change.
- A manual deadline was added successfully.
- The new deadline appeared in the review list.

Learning:

- User testing exposed a discoverability problem in the original inline editor.
- A focused form with Save and Cancel actions was easier to understand.
- Editing and manual additions use the same conflict-analysis workflow.

Result: **Passed**

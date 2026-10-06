# Test Cases

## TC-01: Open the website

Steps:
1. Open the Risalah website.
2. Wait for the homepage to load.

Expected Result:
- The homepage loads successfully.
- No blank page or loading error appears.

Status:
Pass

Actual Result:
The homepage loaded successfully without errors.

---

## TC-02: Change language

Steps:
1. Open the language selector.
2. Select English.

Expected Result:
- The interface changes to English.
- The page layout remains correct.

Status:
Fail

Actual Result:
The interface changed to English, but some Arabic text is still displayed in the map and event list..

---

## TC-03: Open AI guide for a historical station

Steps:
1. Open the Journey & Map page.
2. Select a historical station.
3. Open the AI guide.

Expected Result:
- The AI guide opens successfully.
- Suggested questions related to the selected station are displayed.

Status:
Pass

Actual Result:
The AI guide opened successfully and displayed suggested questions related to the selected historical station.

---

## TC-04: Select a predefined historical question

Steps:
1. Open the AI guide.
2. Select one of the suggested historical questions.

Expected Result:
- The selected question is processed successfully.
- A relevant answer is displayed.

Status:
Pass

Actual Result:
The selected suggested question was processed successfully and a relevant answer was displayed.

---

## TC-05: Answer matches the selected question

Steps:
1. Select a suggested question.
2. Read the returned answer.

Expected Result:
- The answer should match the selected question.
- The answer should be relevant to the current historical context.

Status:
Pass

Actual Result:
The returned answer matched the selected question and was relevant to the historical context.

---

## TC-06: Open Interactive Atlas

Steps:
1. Open the homepage.
2. Open the Interactive Atlas.

Expected Result:
- The atlas loads successfully.
- No visual or loading errors appear.

Status:
Pass

Actual Result:
The Interactive Atlas loaded successfully without visual or loading errors.

---

## TC-07: Select a historical station

Steps:
1. Open the Interactive Atlas.
2. Select one historical station.

Expected Result:
- The selected station opens correctly.
- Related historical information is displayed.

Status:
Pass

Actual Result:
The selected historical station opened correctly and the related historical information was displayed.

---

## TC-08: Navigate between stations

Steps:
1. Open the Interactive Atlas.
2. Move from one station to another.

Expected Result:
- Navigation works correctly.
- The displayed content updates according to the selected station.

Status:
Pass

Actual Result:
Navigation between historical stations worked correctly and the displayed content updated according to the selected station.

---

## TC-09: Time period interaction

Steps:
1. Open the Interactive Atlas.
2. Select a different time period.

Expected Result:
- The selected historical period updates correctly.
- The displayed content changes according to the selected period.

Status:
Pass

Actual Result:
The time period filter worked correctly and the displayed historical content updated according to the selected period.

---

## TC-10: Suggested questions change by station

Steps:
1. Open the AI guide in one historical station.
2. Note the suggested questions.
3. Move to another historical station.
4. Open the AI guide again.

Expected Result:
- Suggested questions should change according to the selected station.

Status:
Pass

Actual Result:
The suggested questions changed correctly according to the selected historical station.

---

## TC-11: All suggested questions return answers

Steps:
1. Open the AI guide.
2. Test all suggested questions available in the selected station.

Expected Result:
- Every suggested question returns an answer.
- No question causes an error.

Status:
Pass

Actual Result:
All suggested questions returned answers successfully without errors.

---

## TC-12: Source or reference is displayed

Steps:
1. Select a suggested historical question.
2. Wait for the answer.

Expected Result:
- A source or reference should be displayed with the answer when available.

Status:
Pass

Actual Result:
The answer was displayed together with the related source/reference.

---

## TC-13: Source is relevant to the answer

Steps:
1. Select a suggested question.
2. Review the answer and its source/reference.

Expected Result:
- The displayed source should be related to the answer.

Status:
Pass

Actual Result:
The displayed source/reference was relevant to the answer.

---

## TC-14: AI guide remains linked to current station

Steps:
1. Select a historical station.
2. Open the AI guide.
3. Select a suggested question.

Expected Result:
- The answer should remain related to the current station.

Status:
Pass

Actual Result:
The AI guide returned an answer related to the currently selected historical station.

---

## TC-15: Arabic language interface

Steps:
1. Select Arabic from the language selector.

Expected Result:
- The interface displays Arabic correctly.
- Arabic text direction is displayed properly.

Status:
Pass

Actual Result:
The Arabic interface displayed correctly with proper right-to-left text direction and layout.

---

## TC-16: English language interface

Steps:
1. Select English from the language selector.

Expected Result:
- The interface displays English correctly.
- No Arabic interface text should remain.
- The page layout should remain correct.

Status:
Fail

Actual Result:
The interface changed to English, but some Arabic text remained visible in the map and event-related content.

Related Bug:
BUG-001

---

## TC-17: AI guide questions follow selected language

Steps:
1. Open the AI guide.
2. Change the interface language.
3. Review the suggested questions.

Expected Result:
- Suggested questions should appear in the selected language.

Status:
Pass

Actual Result:
The suggested AI guide questions appeared correctly in the selected language.

---

## TC-18: AI answer follows selected language

Steps:
1. Select a language.
2. Open the AI guide.
3. Select a suggested question.

Expected Result:
- The AI answer should be displayed in the selected language.

Status:
Pass

Actual Result:
The AI answer was displayed correctly in the selected language.

---

## TC-19: AI guide content changes between stations

Steps:
1. Open the AI guide in one station.
2. Move to another station.
3. Open the AI guide again.

Expected Result:
- Questions and answers should reflect the new station.
- Previous station content should not remain incorrectly.

Status:
Pass

Actual Result:
The AI guide content updated correctly when moving between historical stations.

---

## TC-20: Complete guided journey flow

Steps:
1. Open the Journey & Map page.
2. Select a historical station.
3. Open the AI guide.
4. Select a suggested question.
5. Read the answer and source.
6. Move to another historical station and repeat.

Expected Result:
- The complete user flow works without errors.
- Station, question, answer, and source remain contextually connected.

Status:
Pass

Actual Result:
The complete guided journey worked successfully, and the station, suggested question, answer, and source remained contextually connected.
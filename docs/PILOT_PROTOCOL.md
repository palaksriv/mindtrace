# MindTrace pilot study protocol (draft)

Purpose: turn the prototype into an evaluated system. Everything the paper lists
as "future work" is operationalised here so results can be added to a journal or
extended-conference version. **Obtain approval from your institution's ethics
committee (IEC/IRB) before recruiting anyone.**

## 1. Research questions

| ID | Question | Primary measure |
|----|----------|-----------------|
| RQ1 | Is the 20-item instrument internally consistent and stable? | Cronbach's alpha per trait (95 % bootstrap CI); test-retest *r* at 1-2 weeks |
| RQ2 | Does it agree with an established short Big Five measure? | Pearson *r* against BFI-10 per trait (convergent validity) |
| RQ3 | Do counsellors find the report understandable and useful? | SUS (usability) + semi-structured interviews |
| RQ4 | Are the behavioural indicators stable and usable across recording conditions? | Face-presence %, effective sampling rate, data-quality status by condition (glasses, lighting, device) |
| RQ5 | Where should the deviation-index cut-offs sit? | Empirical distribution of the index (percentiles), counsellor-rated usefulness of cues |
| RQ6 | Do indicators perform evenly across groups? | Face-presence and index distributions by self-reported glasses / head covering / lighting |

## 2. Participants

* **Students:** aim for n >= 60 (n >= 100 gives a much tighter alpha interval). At least 20 complete a second session after 7-14 days for test-retest.
* **Counsellors:** 3-6, each reviewing at least 5 anonymised reports.
* Inclusion: adult students who consent. Exclusion: anyone who declines the webcam (they may still take the questionnaire; their sessions simply have no telemetry).

## 3. Procedure

1. Participant reads the information sheet and consent form (template in section 6).
2. Completes the BFI-10 (external measure, entered by the researcher with the participant's pseudonym).
3. Takes the MindTrace assessment in the app. Consent is recorded per session (`consent_records`).
4. Short questionnaire on recording conditions (glasses, head covering, lighting, device, camera position).
5. After 7-14 days, a subset repeats the MindTrace assessment.
6. Counsellors review anonymised reports, then complete the SUS and a 20-30 minute interview.

## 4. Analysis plan (pre-specify before looking at data)

```bash
export MINDTRACE_EXPORT_SALT="<random secret stored separately from the data>"
python -m scripts.export_pilot_data --out exports
python -m scripts.reliability_report --items exports/item_responses.csv \
    --sessions exports/session_summary.csv --bfi10 exports/bfi10_scores.csv
```

* RQ1: report alpha with CI. With four items per trait, alpha will likely be modest; the report also prints the Spearman-Brown prediction for an 8-item scale so the paper can justify lengthening the instrument if needed.
* RQ2: correlation between each MindTrace trait and the matching BFI-10 trait (convergent validity); report neuroticism direction carefully.
* RQ4/RQ6: descriptive statistics and box plots by condition; avoid claiming "no difference" from small subgroups.
* RQ5: choose new `AnalyticsConfig` thresholds from percentiles of the pilot distribution (for example the 75th and 95th percentile), record them in the paper, and re-run the synthetic tests. These are **relative** cut-offs; they are not clinical thresholds.
* RQ3: SUS scored as usual; thematic summary of interviews.

## 5. What you can and cannot claim afterwards

* Can claim: measured reliability, agreement with BFI-10, usability findings, data-quality behaviour, empirical calibration of cues.
* Cannot claim: detection of stress, emotion, deception or mental-health status. The system does not measure those and the pilot design cannot support such claims.

## 6. Consent form (template - adapt to your institution)

> **MindTrace research study.** You are invited to complete a short personality-style questionnaire while your webcam observes simple movement signals (whether your face is visible, where your head is turned, blinking and head movement).
> * Your video is **not recorded or uploaded**. Your device converts each camera frame into a few numbers and discards the frame; only those numbers and your answers are stored.
> * Your data are stored under a random code, not your name, for analysis. Camera-derived numbers are deleted after [30] days; your answers are kept for [period].
> * The output is descriptive and **is not a diagnosis or a judgement about you**. Taking part is voluntary, does not affect your grades or services, and you may stop or withdraw at any time.
> * Contact: [researcher name, email]. Ethics approval: [reference].
> [ ] I have read the above and agree to take part, including use of my webcam.

## 7. Data management checklist

- [ ] Ethics approval reference obtained
- [ ] `MINDTRACE_EXPORT_SALT` stored separately from exported data
- [ ] Retention job scheduled: `python -m scripts.purge_telemetry --older-than-days 30`
- [ ] `MINDTRACE_ALLOW_DATA_WIPE=false` and a strong `MINDTRACE_JWT_SECRET` in the study deployment
- [ ] Counsellor accounts created with the invite code, not shared

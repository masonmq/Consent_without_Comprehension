<h1 align="center"> Consent without Comprehension: A Randomized Experiment on Pedagogical Friction 
  
  in Privacy Policy Flows</h1>

<p align="center">
  <img src="study_flow.png" width="81%">
</p>


## 🔍 Overview

Privacy policies govern how data is collected, used, and shared, yet agreement is often operationalized as a single click. Privacy-law scholarship argues for demonstrably informed consent, requiring evidence that a person understands consequential terms. We study pedagogical friction as a design framing: minimal interventions embedded within a privacy-policy consent flow to support demonstrated comprehension while keeping user burden low. In a randomized experiment with 293 parents, we tested six conditions varying presentation and pacing. The timed slide-based condition (G3) had the highest observed first-attempt threshold attainment (>=80%) (41.7%), followed by the paced, sectioned condition (G4) (30.6%). Among retakers, 66.4\% improved after a second policy review and quiz attempt. In our ungated study conditions, 97.3% of participants who did not meet the comprehension threshold chose to consent. Our results show that some forms of pedagogical friction can support demonstrated comprehension at different stages, with varying time and burden costs.

The scripts listed below reproduce the analyses reported in the paper.

---

## 🚀 Analysis scripts

### 1. RQ1: How does demonstrated comprehension of key terms vary across privacy-policy review designs with different forms of pedagogical friction?

**Quiz performance by condition**

- `quiz_performance.py`  
  - First attempt accuracy.
  - First attempt threshold attainment.
- `quiz_difficulty.py`  
  - The hardest and easiest questions.
  - The hardest to correct questions.

**Retake outcomes for conditions with a second attempt**

- `compute_retry_answer.py`  
  - Second attempt accuracy.
  - Second attempt threshold attainment.
  - Retake gains
  - Error correction analysis

---

### 2. RQ2: What costs accompany frictional interventions and how are they tolerated by users?

**Time cost**

- `compute_time_spend.py`  
  - Analyze first-attempt quiz completion time.
  - Second-attempt quiz completion time.
  - Analyze first-attempt policy review time.
  - Second-attempt policy review time.

**User tolerance of friction**

- `survey_accuracy.py`  
  - Analyze how participants tolerated the interventions.

---

### 3. Consent Decisions

**Consent rate**

- `consent_analysis.py`  
  - Consent among participants who met the threshold.
  - Consent among participants unmet the threshold.


---

## 📊 Usage and data

### 1. Each script contains:
- Expected input data files.
- Any preprocessing steps required before running the analysis.

### 2. To replicate results, please:
1. Place the analysis dataset in the paths expected by the scripts.
2. Run the relevant script(s) with your preferred Python environment.

   



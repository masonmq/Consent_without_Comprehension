<h1 align="center"> Consent with Comprehension: A Randomized Experiment on Pedagogical Friction 
  
  in Privacy Policy Flows</h1>

<p align="center">
  <img src="study_flow.png" width="81%">
</p>


## 🔍 Overview

Privacy policies are meant to inform people about how their data will be collected, used, and shared, yet consent is often reduced to clicking 'I agree.' We ask whether pedagogical friction--brief interventions that slow users down, focus attention, or explain important terms--can improve understanding of consequential terms without excessive burden. In a randomized experiment with 293 parents evaluating a children’s learning app, we test six interface designs, from a standard text policy to versions using highlighting, plain-language explanations, pacing, sectioning, and timed slide recap. Participants completed a comprehension quiz; in three conditions, those scoring below 80% reviewed the policy and retook the quiz. The slide recap condition had the highest first-attempt passing rate (41.7%), and 66.4% of retakers improved. In ungated conditions, 97.3% of participants below the comprehension threshold still consented. These findings suggest that targeted friction can support comprehension while highlighting the gap between recorded agreement and demonstrated understanding.

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

   



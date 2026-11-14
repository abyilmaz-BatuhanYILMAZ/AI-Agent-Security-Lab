# Peer-reviewed publications — Android malware detection

Two published research papers by **Abdullah Batuhan Yilmaz**, **Yavuz Selim Taspinar**, and **Murat Koklu** document earlier work on machine-learning-based Android malware classification. They predate, and are methodologically separate from, the LLM agent security evaluations in this repository.

The purpose of this page is to provide independently verifiable scholarly references, not to suggest that the publications evaluated language-model agents.

## 2026 — Android malware classification and feature selection

**Yilmaz, A. B., Taspinar, Y. S., & Koklu, M. (2026).** *Classification of malicious android applications by machine learning methods using permission properties.* **International Journal of Mobile Communications**, 28(1), 1–22.

- **Publisher article DOI:** [10.1504/IJMC.2026.154630](https://doi.org/10.1504/IJMC.2026.154630)
- **Early-online DOI also listed in institutional records:** [10.1504/IJMC.2026.10075550](https://doi.org/10.1504/IJMC.2026.10075550)
- **Published online:** 8 July 2026
- **Research focus:** Android permission-based malware classification, feature selection with information gain, and evaluation of AdaBoost, Random Forest and artificial neural networks.
- **Dataset reported in the article:** 2,854 malicious and 2,870 benign Android applications.
- **Reported best accuracy:** **98.4%** using an artificial neural network with the full 117-feature representation.
- **Evaluation reported:** precision, recall, F1, ROC/AUC, training and testing time, and feature-correlation analysis.

**Verification:** [Publisher DOI](https://doi.org/10.1504/IJMC.2026.154630) · [Selçuk University publication record](https://avid.selcuk.edu.tr/makale/8512690) · [Scopus-linked institutional metadata](https://avid.selcuk.edu.tr/scopus/13140).

## 2022 — Naive Bayes and SVM for Android malware classification

**Yilmaz, A. B., Taspinar, Y. S., & Koklu, M. (2022).** *Classification of Malicious Android Applications Using Naive Bayes and Support Vector Machine Algorithms.* **International Journal of Intelligent Systems and Applications in Engineering**, 10(2), 269–274.

- **Journal page:** [IJISAE article 2010](https://www.ijisae.org/index.php/IJISAE/article/view/2010)
- **Published:** 27 May 2022
- **Research focus:** Android malware classification using permission features with support vector machines (SVM) and Naive Bayes (NB).
- **Dataset reported in the article:** 2,854 malicious and 2,870 benign applications, 116 permission features and one class field.
- **Evaluation reported:** 10-fold cross-validation, accuracy, precision, recall, specificity, F1 and ROC/AUC.
- **Reported classification accuracies:** **90.9% (SVM)** and **92.4% (NB)**.

**Verification:** [Official journal record](https://www.ijisae.org/index.php/IJISAE/article/view/2010).

## Relationship to AI agent security research

These publications demonstrate prior experience with:

1. Framing and evaluating cybersecurity problems using real-world application metadata.
2. Preparing features and performing classification experiments.
3. Comparing machine-learning algorithms and documenting multiple evaluation metrics.
4. Publishing technical research in peer-reviewed journals.

The present [AI Agent Security Lab](../README.md) applies the broader practice of reproducible evaluation to a **different problem**: security boundaries between lower-trust text, LLM decisions, and authorized tool actions.

**Important methodological note:** The 2022 and 2026 accuracy values are reported from their respective papers. They are **not** results from this repository and must not be interpreted as a controlled head-to-head improvement without checking dataset splits, validation schemes, feature selection and experimental conditions.

This repository does not redistribute the articles' copyrighted publisher PDFs, any APK datasets, or model weights from those studies. Follow each publisher's access and reuse terms.

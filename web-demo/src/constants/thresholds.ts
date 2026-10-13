/**
 * Single confidence threshold constant shared across backend and frontend.
 * Evaluated on held-out test set: tau=0.03, threshold=0.65 gives 86.5% Precision, 80.4% Recall, 85.0% OOD Rejection.
 */
export const CONFIDENCE_THRESHOLD = 0.65;
export const CONFIDENCE_THRESHOLD_PERCENT = Math.round(CONFIDENCE_THRESHOLD * 100);

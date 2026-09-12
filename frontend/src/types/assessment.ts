export interface AssessmentSummary { id: number; title: string; description: string; question_count: number }
export interface Question { id: number; question_text: string; trait: string; order: number }
export interface AssessmentDetail { id: number; title: string; description: string; questions: Question[] }
export interface AssessmentSession { id: number; assessment_id: number; status: string; started_at: string }
export interface Results { session_id: number; trait_scores: Record<string, number> }

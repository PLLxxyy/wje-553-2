import { request } from '../utils/request';
import type { GradeStatus } from '../constants/enums';

export interface GradeSummary { average: number; highest: number; lowest: number; pass_rate: number; rows: unknown[] }

export interface GradedSubmission {
  id: string;
  assignment_id: string;
  student_id: string;
  student_name: string | null;
  score: number | null;
  comment: string | null;
  grade_status: GradeStatus;
  graded_at: string | null;
  submitted_at: string | null;
}

export interface ComprehensiveResult {
  course_id: string;
  student_id: string;
  comprehensive_score: number;
}

export const gradeApi = {
  summary: (course_id?: string) => request.get<unknown, GradeSummary>('/grades/summary', { params: { course_id } }),
  listGraded: (params?: { assignment_id?: string; grade_status?: GradeStatus }) => request.get<unknown, GradedSubmission[]>('/grades/submissions', { params }),
  grade: (submission_id: string, data: { score: number; comment?: string }) => request.post<unknown, GradedSubmission>(`/grades/${submission_id}/grade`, data),
  publish: (data: { assignment_id?: string; submission_ids?: string[] }) => request.post<unknown, { published_count: number }>('/grades/publish', data),
  comprehensive: (course_id: string, student_id: string) => request.get<unknown, ComprehensiveResult>(`/grades/comprehensive/${course_id}/${student_id}`),
};

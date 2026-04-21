export type TracingProject = {
  id: string;
  name: string;
  created_at: string;
  modified_at: string;
};

export type Trace = {
  id: string;
  project_id: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  trace_metadata: Record<string, any>;
  start_time: string;
  end_time: string;
};

export type Queue = {
  id: string;
  name: string;
  created_at: string;
  modified_at: string;
};

export type QueueEntry = {
  id: string;
  trace_id: string;
  queue_id: string;
  status: string;
  added_at: string;
  trace: Trace;
};

export type QueueRubricItem = {
  id: string;
  queue_id: string;
  feedback_key: string;
  description: string;
};

export type FeedbackSpan = {
  span_path: (string | number)[];
  span_start_index?: number;
  span_end_index?: number;
};

export type Feedback = {
  id: string;
  trace_id: string;
  key: string;
  score: number | null;
  comment: string | null;
  span_path?: (string | number)[];
  span_start_index?: number;
  span_end_index?: number;
  created_at: string;
  modified_at: string;
};

export type FeedbackCreate = {
  trace_id: string;
  key: string;
  score?: number;
  comment?: string;
  span?: FeedbackSpan;
};

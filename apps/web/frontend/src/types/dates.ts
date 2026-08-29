export type DateEventStatus = "planned" | "scheduled" | "done";
export type DateMemoryKind = "photo" | "note";
export type DateRelationStatus = "couple" | "married";
export type DateCoupleStatus = "active" | "archived";
export type DateMilestoneType = "monthly" | "anniversary" | "wedding" | "custom";

export interface DateCouple {
  id: number;
  member_ids: number[];
  started_at: string | null;
  relationship_status: DateRelationStatus;
  status: DateCoupleStatus;
  created_at: string;
  updated_at: string;
}

export interface DateMilestone {
  id: number;
  couple_id: number;
  type: DateMilestoneType;
  date: string;
  label: string;
  notes: string | null;
  created_at: string;
}

export interface DateAttribute {
  id: number;
  key: string;
  value: string;
  is_secret: boolean;
  reveal_on: string | null;
}

export interface DateEvent {
  id: number;
  couple_id: number;
  week_start: string;
  planned_by: number;
  scheduled_date: string | null;
  scheduled_time: string | null;
  title: string | null;
  status: DateEventStatus;
  created_at: string;
  updated_at: string;
  attributes: DateAttribute[];
}

export interface DateMemory {
  id: number;
  event_id: number;
  kind: DateMemoryKind;
  media_url: string | null;
  caption: string | null;
  taken_by: number | null;
  created_at: string;
}

export interface CreateCoupleInput {
  member_ids: number[];
  started_at?: string | null;
  relationship_status?: DateRelationStatus;
}

export type UpdateCoupleInput = Partial<{
  member_ids: number[];
  started_at: string | null;
  relationship_status: DateRelationStatus;
  status: DateCoupleStatus;
}>;

export interface CreateMilestoneInput {
  type: DateMilestoneType;
  date: string;
  label: string;
  notes?: string | null;
}

export interface CreateEventInput {
  couple_id: number;
  week_start: string;
  planned_by?: number | null;
  title?: string | null;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  attributes?: Array<{
    key: string;
    value: string;
    is_secret?: boolean;
    reveal_on?: string | null;
  }>;
}

export type UpdateEventInput = Partial<{
  planned_by: number | null;
  title: string | null;
  scheduled_date: string | null;
  scheduled_time: string | null;
  attributes: Array<{
    key: string;
    value: string;
    is_secret?: boolean;
    reveal_on?: string | null;
  }>;
}>;

export interface AddMemoryInput {
  kind: DateMemoryKind;
  media_url?: string | null;
  caption?: string | null;
  taken_by?: number | null;
}
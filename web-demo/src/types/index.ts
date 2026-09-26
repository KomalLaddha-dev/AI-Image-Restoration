/**
 * Type definitions for Heritage Restore web client.
 */

export interface SourceCitation {
  name: string;
  url?: string | null;
}

export interface TimelineEvent {
  year: string;
  event: string;
}

export interface RelatedImage {
  url: string;
  caption?: string;
  is_archival?: boolean;
  is_restored?: boolean;
}

export interface HistoryResponse {
  monument_id: string;
  name: string;
  summary: string;
  era?: string | null;
  builder?: string | null;
  architectural_style?: string | null;
  unesco_status?: string | null;
  location?: string | null;
  coordinates?: [number, number] | null;
  sources: SourceCitation[];
  timeline: TimelineEvent[];
  related_images?: (RelatedImage | string)[];
  archival_image_url?: string;
  restored_reference_url?: string;
}

export interface IdentifyResponse {
  monument_id: string;
  monument_name: string;
  confidence: number;
  location?: string | null;
  era?: string | null;
  thumbnail_url?: string | null;
  recognized: boolean;
}

export interface IdentifyNotRecognizedResponse {
  recognized: false;
  message: string;
  confidence: number;
  suggestions?: string[];
}

export type IdentifyResultData = IdentifyResponse | IdentifyNotRecognizedResponse;

export interface RestoreOptions {
  denoise: boolean;
  colorize: boolean;
  face_restore: boolean;
}

export interface RestoreResult {
  blob: Blob;
  url: string;
  processingTime: number;
  stages: string[];
}

export type ThemeMode = 'light' | 'dark';

export interface BeforeAfterSliderProps {
  beforeSrc: string;
  afterSrc: string;
  beforeLabel?: string;
  afterLabel?: string;
  className?: string;
  aspectRatio?: string;
  autoAnimate?: boolean;
}

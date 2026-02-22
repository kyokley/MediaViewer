// API Response types
export interface ApiResponse<T = unknown> {
  data: T;
  pagination?: {
    total: number;
    limit: number;
    offset: number;
  };
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

// User types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  avatar_url?: string;
}

export interface UserSettings {
  id: number;
  dark_theme: boolean;
  items_per_page: number;
  autoplay_next: boolean;
  default_quality: string;
  subtitle_language: string;
  volume_level: number;
  email_notifications: boolean;
  created_at: string;
  updated_at: string;
}

// Media types
export interface Genre {
  id: number;
  name: string;
  datecreated: string;
  dateedited: string;
}

export interface Movie {
  id: number;
  title: string;
  name: string;
  date_created: string;
  dateedited: string;
  poster_image?: string;
  poster_image_url?: string;
  description?: string;
  release_date?: string;
  genres: Genre[];
}

export interface TVShow {
  id: number;
  title: string;
  name: string;
  date_created: string;
  dateedited: string;
  poster_image?: string;
  poster_image_url?: string;
  description?: string;
  first_air_date?: string;
  genres: Genre[];
}

export interface TV extends TVShow {}

// Episode types
export interface Episode {
  id: number;
  season: number;
  episode: number;
  display_name: string;
  episode_name?: string;
  date_created: string;
  watched: boolean;
}

export interface Season {
  season_number: number;
  episodes: Episode[];
}

export interface EpisodesResponse {
  data: Season[];
  total_episodes: number;
  total_seasons: number;
}

// Collection types
export interface Collection {
  id: number;
  name: string;
  item_count: number;
}

// Request types
export interface MediaRequest {
  id: number;
  name: string;
  done: boolean;
  user_username: string;
  vote_count: number;
  datecreated: string;
  dateedited: string;
}

export type Request = MediaRequest;

// Video progress types
export interface VideoProgress {
  id: number;
  hashed_filename: string;
  offset: number;
  date_edited: string;
  movie_name?: string;
  media_file_name?: string;
}

// Comment types
export interface Comment {
  id: number;
  user_username: string;
  movie_name?: string;
  media_file_name?: string;
  viewed: boolean;
  date_created: string;
  date_modified: string;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh: string;
}

export interface RefreshTokenResponse {
  access: string;
  refresh?: string;
}
